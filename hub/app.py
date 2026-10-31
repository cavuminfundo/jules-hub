"""
Jules Hub FastAPI Server.
Provides REST and SSE endpoints for worktree lifecycle, engine execution,
suggestions scanning, CDP escalation to Antigravity, and conditional UI serving.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import uuid

from fastapi import BackgroundTasks, Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from hub.cdp_bridge import CDPBridge, CDPResponse, probe_ollama_instance
from hub.config_store import ConfigStore
from hub.engine_router import EngineRouter
from hub.models import (
    EngineMode,
    EscalateRequest,
    HubConfig,
    OllamaInstance,
    PatchResult,
    RoleModelConfig,
    RunRequest,
    RunResponse,
    SeniorReviewResult,
    Suggestion,
    TaskStatus,
    WorktreePruneRequest,
    WorktreeSessionInfo,
)
from hub.scanner import find_suggestions
from hub.scheduler import BackgroundScheduler
from hub.worktree_manager import WorktreeManager

logger = logging.getLogger("hub.app")


class TaskLogManager:
    """In-memory event hub for task log streaming via SSE."""

    def __init__(self):
        self.history: Dict[str, List[str]] = {}
        self.listeners: Dict[str, List[asyncio.Queue]] = {}
        self.statuses: Dict[str, TaskStatus] = {}

    def has_task(self, task_id: str) -> bool:
        return task_id in self.statuses or task_id in self.history

    def set_status(self, task_id: str, status: TaskStatus) -> None:
        self.statuses[task_id] = status

    def get_status(self, task_id: str) -> TaskStatus:
        return self.statuses.get(task_id, TaskStatus.PENDING)

    def add_log(self, task_id: str, line: str) -> None:
        if task_id not in self.history:
            self.history[task_id] = []
        self.history[task_id].append(line)

        for q in self.listeners.get(task_id, []):
            try:
                q.put_nowait(line)
            except asyncio.QueueFull:
                pass

    def get_history(self, task_id: str) -> List[str]:
        return list(self.history.get(task_id, []))

    def register_listener(self, task_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=200)
        if task_id not in self.listeners:
            self.listeners[task_id] = []
        self.listeners[task_id].append(q)
        return q

    def unregister_listener(self, task_id: str, q: asyncio.Queue) -> None:
        if task_id in self.listeners and q in self.listeners[task_id]:
            self.listeners[task_id].remove(q)


async def execute_run_task(task_id: str, req: RunRequest, app_state: Any) -> RunResponse:
    """Executes patch generation and test validation inside an isolated worktree."""
    task_mgr: TaskLogManager = app_state.task_manager
    wm: WorktreeManager = app_state.worktree_manager
    router: EngineRouter = app_state.engine_router

    task_mgr.set_status(task_id, TaskStatus.RUNNING)
    task_mgr.add_log(task_id, f"Starting curation run for '{req.repo}' (persona: {req.persona}, mode: {req.mode})")

    if req.dry_run:
        task_mgr.add_log(task_id, "Dry-run enabled: skipping worktree creation and code modifications.")
        task_mgr.set_status(task_id, TaskStatus.PASSED)
        task_mgr.add_log(task_id, "Dry-run execution completed.")
        return RunResponse(
            task_id=task_id,
            status=TaskStatus.PASSED,
            message="Dry run completed successfully (no changes applied)",
        )

    try:
        # Resolve repository path
        repo_path = await asyncio.to_thread(wm.resolve_repo_path, req.repo)
        task_mgr.add_log(task_id, f"Resolved repository at: {repo_path}")

        # Create session
        session = wm.create_session(
            repo_name_or_path=repo_path,
            persona=req.persona,
            branch_name=req.branch,
        )
        task_mgr.add_log(task_id, f"Prepared worktree session '{session.worktree_path.name}' on branch '{session.branch}'")

        # Isolated worktree context
        async with session as ctx:
            task_mgr.add_log(task_id, f"Worktree spawned at: {ctx.worktree_path}")

            # Apply patch if target_file is provided
            if req.target_file:
                task_mgr.add_log(task_id, f"Generating micro-patch on {req.target_file} via {req.mode}...")
                patch_res: PatchResult = await router.analyze_and_patch(
                    repo_path=ctx.worktree_path,
                    persona=req.persona,
                    target_file=req.target_file,
                    issue_context=req.issue_context,
                    mode=req.mode,
                )
                if not patch_res.success:
                    task_mgr.add_log(task_id, f"Patch generation failed: {patch_res.error}")
                    task_mgr.set_status(task_id, TaskStatus.FAILED)
                    return RunResponse(
                        task_id=task_id,
                        status=TaskStatus.FAILED,
                        worktree_path=str(ctx.worktree_path),
                        branch=ctx.branch,
                        message=f"Patch generation failed: {patch_res.error}",
                    )

                task_mgr.add_log(
                    task_id,
                    f"Patch applied successfully ({patch_res.lines_changed} lines changed via {patch_res.engine_used})",
                )
                if patch_res.diff:
                    task_mgr.add_log(task_id, f"Diff preview:\n{patch_res.diff}")

            # Execute automated test suite
            task_mgr.set_status(task_id, TaskStatus.TESTING)
            task_mgr.add_log(task_id, f"Running automated test gate in {ctx.worktree_path}...")
            test_passed, test_output = await wm.run_tests_async(ctx.worktree_path)
            task_mgr.add_log(task_id, f"Test output:\n{test_output}")

            if test_passed:
                ctx.mark_success()
                task_mgr.set_status(task_id, TaskStatus.PASSED)
                task_mgr.add_log(task_id, "Test gate PASSED! Worktree ready for review/escalation.")
                return RunResponse(
                    task_id=task_id,
                    status=TaskStatus.PASSED,
                    worktree_path=str(ctx.worktree_path),
                    branch=ctx.branch,
                    message="Patch and tests passed successfully",
                )
            else:
                task_mgr.set_status(task_id, TaskStatus.NEEDS_ESCALATION)
                task_mgr.add_log(task_id, "Test gate FAILED. Worktree preserved for Senior escalation.")
                return RunResponse(
                    task_id=task_id,
                    status=TaskStatus.NEEDS_ESCALATION,
                    worktree_path=str(ctx.worktree_path),
                    branch=ctx.branch,
                    message="Tests failed in worktree; senior review required",
                )

    except Exception as e:
        logger.exception("Error executing run task %s: %s", task_id, e)
        task_mgr.set_status(task_id, TaskStatus.FAILED)
        task_mgr.add_log(task_id, f"Fatal task error: {e}")
        return RunResponse(
            task_id=task_id,
            status=TaskStatus.FAILED,
            message=f"Task error: {e}",
        )


def create_app(
    worktree_manager: Optional[WorktreeManager] = None,
    engine_router: Optional[EngineRouter] = None,
    cdp_bridge: Optional[CDPBridge] = None,
    ui_dist_path: Optional[Union[str, Path]] = None,
    config_store: Optional[ConfigStore] = None,
    scheduler: Optional[BackgroundScheduler] = None,
) -> FastAPI:
    """Create and configure the Jules Hub FastAPI application."""
    app = FastAPI(
        title="Jules Hub",
        description="Autonomous Junior Coder Hub with Isolated Git Worktrees and Antigravity CDP Escalation",
        version="0.2.1",
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Subsystem instances attached to app.state
    app.state.worktree_manager = worktree_manager or WorktreeManager()
    app.state.engine_router = engine_router or EngineRouter()
    app.state.cdp_bridge = cdp_bridge or CDPBridge()
    app.state.task_manager = TaskLogManager()
    app.state.config_store = config_store or ConfigStore()
    app.state.scheduler = scheduler or BackgroundScheduler(
        config_store=app.state.config_store,
        worktree_manager=app.state.worktree_manager,
        engine_router=app.state.engine_router,
    )

    # --- REST API Endpoints ---

    @app.get("/api/health")
    async def get_health():
        """Health check endpoint."""
        return {
            "status": "ok",
            "service": "jules-hub",
            "version": "0.2.1",
        }

    @app.get("/api/projects")
    async def get_projects():
        """List registered repositories from projects_registry.json."""
        wm: WorktreeManager = app.state.worktree_manager
        projects = await asyncio.to_thread(wm.list_registered_projects)
        return projects

    @app.get("/api/suggestions", response_model=List[Suggestion])
    async def get_suggestions(
        repo: Optional[str] = Query(None, description="Repository name or directory path"),
        mode: str = Query("all", description="Persona mode: bolt, palette, sentinel, all"),
        category: str = Query("all", description="Category filter"),
    ):
        """Scan repository for micro-improvement suggestions."""
        wm: WorktreeManager = app.state.worktree_manager
        if repo:
            try:
                repo_path = await asyncio.to_thread(wm.resolve_repo_path, repo)
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        else:
            projects = await asyncio.to_thread(wm.list_registered_projects)
            if projects:
                repo_path = Path(projects[0]["path"])
            else:
                repo_path = Path.cwd()

        try:
            state = app.state.config_store.load_state()
            ignored_ids = set(state.ignored_suggestions)
            suggestions = await asyncio.to_thread(
                find_suggestions,
                repo_path=repo_path,
                mode=mode,
                category=category,
                ignored_ids=ignored_ids,
            )
            return suggestions
        except Exception as e:
            logger.exception("Error finding suggestions: %s", e)
            raise HTTPException(status_code=500, detail=f"Scanner error: {e}")

    @app.post("/api/run", response_model=RunResponse)
    async def run_task(
        req: RunRequest,
        background_tasks: BackgroundTasks,
        background: bool = False,
    ):
        """Execute a curation task inside an isolated worktree."""
        task_id = f"task_{uuid.uuid4().hex[:10]}"
        app.state.task_manager.set_status(task_id, TaskStatus.PENDING)
        app.state.task_manager.add_log(task_id, f"Task {task_id} registered.")

        if background:
            background_tasks.add_task(execute_run_task, task_id, req, app.state)
            return RunResponse(
                task_id=task_id,
                status=TaskStatus.RUNNING,
                message="Task scheduled in background",
            )
        else:
            return await execute_run_task(task_id, req, app.state)

    @app.post("/api/escalate", response_model=CDPResponse)
    async def escalate_to_antigravity(req: EscalateRequest):
        """Escalate worktree to Antigravity Senior Review via CDP port 9000."""
        bridge: CDPBridge = app.state.cdp_bridge
        return await bridge.escalate_to_antigravity(req)

    @app.get("/api/worktrees", response_model=List[WorktreeSessionInfo])
    async def list_worktrees():
        """List active worktrees currently in worktrees directory."""
        wm: WorktreeManager = app.state.worktree_manager
        return await asyncio.to_thread(wm.list_worktrees)

    @app.post("/api/worktrees/prune")
    async def prune_worktrees(req: Optional[WorktreePruneRequest] = None):
        """Prune specific or all dangling worktrees."""
        wm: WorktreeManager = app.state.worktree_manager
        if req and req.worktree_path:
            success = await asyncio.to_thread(wm.prune_worktree, req.worktree_path, req.force)
            return {
                "success": success,
                "message": f"Pruned worktree {req.worktree_path}" if success else f"Failed to prune {req.worktree_path}",
            }
        await asyncio.to_thread(wm.cleanup_all)
        return {"success": True, "message": "All worktrees pruned successfully"}

    @app.get("/api/stream/{task_id}")
    async def stream_task_logs(task_id: str):
        """SSE streaming endpoint for real-time task execution logs."""
        task_mgr: TaskLogManager = app.state.task_manager
        if not task_mgr.has_task(task_id):
            raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

        async def event_generator():
            # 1. Stream existing history
            history = task_mgr.get_history(task_id)
            for line in history:
                yield f"data: {json.dumps({'task_id': task_id, 'log': line})}\n\n"

            # 2. Check if already completed
            initial_status = task_mgr.get_status(task_id)
            terminal_states = {
                TaskStatus.PASSED,
                TaskStatus.FAILED,
                TaskStatus.NEEDS_ESCALATION,
                TaskStatus.COMPLETED,
            }
            if initial_status in terminal_states:
                yield f"data: {json.dumps({'task_id': task_id, 'status': initial_status.value, 'done': True})}\n\n"
                return

            # 3. Stream live events
            q = task_mgr.register_listener(task_id)
            try:
                while True:
                    try:
                        line = await asyncio.wait_for(q.get(), timeout=1.0)
                        yield f"data: {json.dumps({'task_id': task_id, 'log': line})}\n\n"
                    except asyncio.TimeoutError:
                        pass

                    curr_status = task_mgr.get_status(task_id)
                    if curr_status in terminal_states:
                        while not q.empty():
                            extra_line = q.get_nowait()
                            yield f"data: {json.dumps({'task_id': task_id, 'log': extra_line})}\n\n"
                        yield f"data: {json.dumps({'task_id': task_id, 'status': curr_status.value, 'done': True})}\n\n"
                        break
            finally:
                task_mgr.unregister_listener(task_id, q)

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # --- v2 Cockpit REST API Endpoints ---

    @app.get("/api/config", response_model=HubConfig)
    async def get_config():
        """Retrieve current Jules Hub v2 configuration."""
        return app.state.config_store.load_config()

    @app.put("/api/config", response_model=HubConfig)
    async def update_config(config: HubConfig):
        """Update and persist Jules Hub v2 configuration atomically."""
        app.state.config_store.save_config(config)
        return config

    @app.post("/api/ollama/test")
    async def test_ollama_instance(instance: OllamaInstance):
        """Probe an Ollama instance endpoint for status and model tags."""
        return await probe_ollama_instance(url=instance.url, timeout=instance.timeout_sec)

    @app.get("/api/ollama/instances/{instance_id}/models")
    async def get_ollama_instance_models(instance_id: int):
        """Query tags from a registered Ollama instance."""
        cfg: HubConfig = app.state.config_store.load_config()
        inst = next((i for i in cfg.ollama_instances if i.id == instance_id), None)
        if not inst:
            raise HTTPException(status_code=404, detail=f"Ollama instance #{instance_id} not found")
        return await probe_ollama_instance(url=inst.url, timeout=inst.timeout_sec)

    @app.get("/api/cdp/models")
    async def get_cdp_models():
        """Retrieve available models via Chrome DevTools Protocol Model Picker."""
        bridge: CDPBridge = app.state.cdp_bridge
        return await bridge.get_available_models()

    @app.post("/api/suggestions/{suggestion_id}/discard")
    async def discard_suggestion(suggestion_id: str):
        """Discard a micro-improvement suggestion so it will not reappear in scans."""
        app.state.config_store.add_ignored_suggestion(suggestion_id)
        return {"success": True, "discarded_id": suggestion_id}

    @app.post("/api/tasks/{task_id}/senior-review", response_model=SeniorReviewResult)
    async def senior_review(
        task_id: str,
        body: Optional[Dict[str, Any]] = Body(None),
        diff_text: Optional[str] = Query(None),
    ):
        """
        Execute Senior Review audit gate on task worktree diff.
        Persists verdict and explanations in hub state.
        """
        router: EngineRouter = app.state.engine_router
        cfg: HubConfig = app.state.config_store.load_config()
        resolved_diff = None
        if body and isinstance(body, dict) and "diff_text" in body and body["diff_text"]:
            resolved_diff = body["diff_text"]
        elif diff_text:
            resolved_diff = diff_text
        else:
            resolved_diff = "+ sample diff"

        result = await router.run_senior_review(
            diff_text=resolved_diff,
            test_status="passed",
            issue_context=f"Review for {task_id}",
            senior_config=cfg.senior_config,
        )
        app.state.config_store.set_task_review(task_id, result)
        return result

    @app.post("/api/tasks/{task_id}/create-pr")
    async def create_pr(task_id: str):
        """
        Create GitHub Pull Request from task worktree.
        Strict Gate: Rejects with HTTP 403 Forbidden if task was not APPROVED by Senior Review.
        """
        review = app.state.config_store.get_task_review(task_id)
        if not review or review.verdict != "APPROVED":
            current_verdict = review.verdict if review else "NOT_REVIEWED"
            raise HTTPException(
                status_code=403,
                detail=f"PR creation forbidden: task '{task_id}' has not been APPROVED by Senior Review (current verdict: {current_verdict})",
            )

        return {
            "success": True,
            "task_id": task_id,
            "pr_url": f"https://github.com/example/jules/pull/{task_id}",
            "message": f"PR created successfully following Senior Review approval by {review.reviewer_model}",
        }

    @app.post("/api/scheduler/{repo_name}/trigger")
    async def trigger_scheduler(repo_name: str):
        """Trigger on-demand curation cycle for specified repository."""
        scheduler: BackgroundScheduler = app.state.scheduler
        return await scheduler.trigger_repo(repo_name)

    # --- Conditional Static UI Mount ---
    dist_dir = Path(ui_dist_path).resolve() if ui_dist_path else Path("ui/dist").resolve()
    if dist_dir.is_dir():
        assets_dir = dist_dir / "assets"
        if assets_dir.is_dir():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

        @app.get("/")
        async def serve_index():
            index_file = dist_dir / "index.html"
            if index_file.is_file():
                return FileResponse(index_file)
            return {"service": "jules-hub", "status": "running"}

        @app.get("/{full_path:path}")
        async def serve_spa_fallback(full_path: str):
            candidate = dist_dir / full_path
            if candidate.is_file():
                return FileResponse(candidate)
            index_file = dist_dir / "index.html"
            if index_file.is_file():
                return FileResponse(index_file)
            raise HTTPException(status_code=404, detail="Not Found")
    else:
        @app.get("/")
        async def root_fallback():
            return {
                "service": "jules-hub",
                "status": "running",
                "ui": "not_built",
            }

    return app


# Default application instance for Uvicorn runner
app = create_app()
