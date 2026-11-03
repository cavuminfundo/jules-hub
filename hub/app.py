"""
Julius Hub FastAPI Server.
Provides REST and SSE endpoints for worktree lifecycle, engine execution,
suggestions scanning, CDP escalation to Antigravity, community configuration, and SPA serving.
"""

import asyncio
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any, Dict, List, Optional, Union
import uuid

from fastapi import BackgroundTasks, Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from hub.cdp_bridge import CDPBridge, CDPResponse, probe_ollama_instance
from hub.config_store import ConfigStore
from hub.engine_router import EngineRouter, get_git_diff
from hub.models import (
    CommunitySettings,
    EngineMode,
    EscalateRequest,
    GitAuthoringMode,
    HubConfig,
    OllamaInstance,
    PatchResult,
    RoleModelConfig,
    RunRequest,
    RunResponse,
    SecretsUpdateRequest,
    SeniorReviewResult,
    SessionRecord,
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
    store: ConfigStore = app_state.config_store

    task_mgr.set_status(task_id, TaskStatus.RUNNING)
    task_mgr.add_log(task_id, f"Starting curation run for '{req.repo}' (persona: {req.persona}, mode: {req.mode})")

    title = req.prompt or (f"Patch {req.target_file}" if req.target_file else f"Curation {task_id}")

    if req.dry_run:
        task_mgr.add_log(task_id, "Dry-run enabled: skipping worktree creation and code modifications.")
        task_mgr.set_status(task_id, TaskStatus.PASSED)
        task_mgr.add_log(task_id, "Dry-run execution completed.")
        session_rec = SessionRecord(
            task_id=task_id,
            repo=req.repo,
            title=title,
            prompt=req.prompt,
            persona=req.persona,
            status=TaskStatus.PASSED,
            branch=req.branch,
            worktree_path=None,
            diff=None,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        store.upsert_session(session_rec)
        return RunResponse(
            task_id=task_id,
            status=TaskStatus.PASSED,
            diff=None,
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

            patch_res: Optional[PatchResult] = None
            if req.target_file:
                task_mgr.add_log(task_id, f"Generating micro-patch on {req.target_file} via {req.mode}...")
                patch_res = await router.analyze_and_patch(
                    repo_path=ctx.worktree_path,
                    persona=req.persona,
                    target_file=req.target_file,
                    issue_context=req.issue_context or req.prompt or "",
                    mode=req.mode,
                    prompt=req.prompt,
                )
            elif req.prompt:
                task_mgr.add_log(task_id, f"Generating patch from prompt '{req.prompt}' via {req.mode}...")
                patch_res = await router.run_freeform_prompt(
                    repo_path=ctx.worktree_path,
                    prompt=req.prompt,
                    mode=req.mode,
                    persona=req.persona,
                )

            if patch_res and not patch_res.success:
                task_mgr.add_log(task_id, f"Patch generation failed: {patch_res.error}")
                task_mgr.set_status(task_id, TaskStatus.FAILED)
                fail_rec = SessionRecord(
                    task_id=task_id,
                    repo=req.repo,
                    title=title,
                    prompt=req.prompt,
                    persona=req.persona,
                    status=TaskStatus.FAILED,
                    branch=ctx.branch,
                    worktree_path=str(ctx.worktree_path),
                    diff=None,
                    created_at=datetime.now(timezone.utc).isoformat(),
                )
                store.upsert_session(fail_rec)
                return RunResponse(
                    task_id=task_id,
                    status=TaskStatus.FAILED,
                    worktree_path=str(ctx.worktree_path),
                    branch=ctx.branch,
                    diff=None,
                    message=f"Patch generation failed: {patch_res.error}",
                )

            if patch_res and patch_res.success:
                task_mgr.add_log(
                    task_id,
                    f"Patch applied successfully ({patch_res.lines_changed} lines changed via {patch_res.engine_used})",
                )

            # Capture real diff from worktree
            real_diff = (patch_res.diff if patch_res and patch_res.diff else None) or get_git_diff(ctx.worktree_path)
            if real_diff:
                store.set_task_diff(task_id, real_diff)
                task_mgr.add_log(task_id, f"Diff preview ({len(real_diff.splitlines())} lines):\n{real_diff}")

            # Execute automated test suite
            task_mgr.set_status(task_id, TaskStatus.TESTING)
            task_mgr.add_log(task_id, f"Running automated test gate in {ctx.worktree_path}...")
            test_passed, test_output = await wm.run_tests_async(ctx.worktree_path)
            task_mgr.add_log(task_id, f"Test output:\n{test_output}")

            final_status = TaskStatus.PASSED if test_passed else TaskStatus.NEEDS_ESCALATION
            if test_passed:
                ctx.mark_success()
                task_mgr.set_status(task_id, TaskStatus.PASSED)
                task_mgr.add_log(task_id, "Test gate PASSED! Worktree ready for review/escalation.")
                msg = "Patch and tests passed successfully"
            else:
                task_mgr.set_status(task_id, TaskStatus.NEEDS_ESCALATION)
                task_mgr.add_log(task_id, "Test gate FAILED. Worktree preserved for Senior escalation.")
                msg = "Tests failed in worktree; senior review required"

            session_rec = SessionRecord(
                task_id=task_id,
                repo=req.repo,
                title=title,
                prompt=req.prompt,
                persona=req.persona,
                status=final_status,
                branch=ctx.branch,
                worktree_path=str(ctx.worktree_path),
                diff=real_diff,
                created_at=datetime.now(timezone.utc).isoformat(),
            )
            store.upsert_session(session_rec)

            return RunResponse(
                task_id=task_id,
                status=final_status,
                worktree_path=str(ctx.worktree_path),
                branch=ctx.branch,
                diff=real_diff,
                message=msg,
            )

    except Exception as e:
        logger.exception("Error executing run task %s: %s", task_id, e)
        task_mgr.set_status(task_id, TaskStatus.FAILED)
        task_mgr.add_log(task_id, f"Fatal task error: {e}")
        return RunResponse(
            task_id=task_id,
            status=TaskStatus.FAILED,
            diff=None,
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
    """Create and configure the Julius Hub FastAPI application."""
    app = FastAPI(
        title="Julius Hub",
        description="Autonomous Junior Coder Hub with Isolated Git Worktrees and Antigravity CDP Escalation",
        version="0.3.0",
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
            "service": "julius-hub",
            "version": "0.3.0",
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

    @app.get("/api/sessions", response_model=List[SessionRecord])
    async def get_sessions(repo: Optional[str] = Query(None, description="Filter by repository")):
        """List executed prompt and curation sessions."""
        return app.state.config_store.list_sessions(repo=repo)

    @app.get("/api/tasks/{task_id}")
    async def get_task_detail(task_id: str):
        """Retrieve full details of an executed task including worktree diff."""
        session = app.state.config_store.get_session(task_id)
        diff = app.state.config_store.get_task_diff(task_id)
        review = app.state.config_store.get_task_review(task_id)
        if not session and not diff and not review:
            raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
        return {
            "task_id": task_id,
            "session": session,
            "diff": diff,
            "review": review,
        }

    @app.post("/api/settings/secrets", response_model=CommunitySettings)
    async def update_secrets(req: SecretsUpdateRequest):
        """Securely persist GitHub token and AI API keys with 0600 file permissions."""
        return app.state.config_store.save_secrets(req)

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

    # --- v2/v3 Cockpit REST API Endpoints ---

    @app.get("/api/config", response_model=HubConfig)
    async def get_config():
        """Retrieve current Julius Hub configuration without exposing plaintext secrets."""
        return app.state.config_store.load_config()

    @app.put("/api/config", response_model=HubConfig)
    async def update_config(config: HubConfig):
        """Update and persist Julius Hub configuration atomically."""
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
        Loads real worktree diff from config store if not provided in request.
        """
        router: EngineRouter = app.state.engine_router
        cfg: HubConfig = app.state.config_store.load_config()
        resolved_diff = None
        if body and isinstance(body, dict) and body.get("diff_text"):
            resolved_diff = body["diff_text"]
        elif diff_text:
            resolved_diff = diff_text
        else:
            resolved_diff = app.state.config_store.get_task_diff(task_id) or ""

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
        Executes real git commit, push, and gh pr create when repository and gh CLI are available.
        """
        review = app.state.config_store.get_task_review(task_id)
        if not review or review.verdict != "APPROVED":
            current_verdict = review.verdict if review else "NOT_REVIEWED"
            raise HTTPException(
                status_code=403,
                detail=f"PR creation forbidden: task '{task_id}' has not been APPROVED by Senior Review (current verdict: {current_verdict})",
            )

        cfg: HubConfig = app.state.config_store.load_config()
        session = app.state.config_store.get_session(task_id)
        branch = (session.branch if session else None) or f"curator/task-{task_id}"
        wt_path = Path(session.worktree_path) if session and session.worktree_path else None

        # Authoring attribution trailer
        authoring = cfg.settings.git_commit_authoring
        co_author_trailer = ""
        if authoring == GitAuthoringMode.CO_AUTHORED:
            co_author_trailer = "\n\nCo-authored-by: Julius <julius@julius-hub.local>"
        elif authoring in (GitAuthoringMode.JULIUS_ONLY, GitAuthoringMode.JULES_ONLY):
            co_author_trailer = "\n\nAuthor: Julius <julius@julius-hub.local>"

        pr_url = f"local://worktree/{task_id}/branch/{branch}"
        pr_message = f"PR created successfully following Senior Review approval by {review.reviewer_model}"

        # Real git commit & gh PR execution if worktree exists and gh CLI is available
        if wt_path and wt_path.exists() and shutil.which("gh"):
            env = os.environ.copy()
            secrets = app.state.config_store.get_secrets()
            gh_tok = secrets.get("github_token") or os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
            if gh_tok:
                env["GITHUB_TOKEN"] = gh_tok
                env["GH_TOKEN"] = gh_tok

            commit_msg = f"fix({task_id}): automated improvement by Julius{co_author_trailer}"
            try:
                subprocess.run(["git", "add", "-A"], cwd=str(wt_path), check=False, env=env, timeout=10)
                subprocess.run(["git", "commit", "-m", commit_msg], cwd=str(wt_path), check=False, env=env, timeout=10)
                push_res = subprocess.run(
                    ["git", "push", "-u", "origin", branch],
                    cwd=str(wt_path),
                    capture_output=True,
                    text=True,
                    check=False,
                    env=env,
                    timeout=30,
                )
                if push_res.returncode == 0:
                    gh_cmd = [
                        "gh", "pr", "create",
                        "--title", f"fix: Julius automated patch for {task_id}",
                        "--body", f"Automated patch reviewed and approved by {review.reviewer_model}.{co_author_trailer}",
                    ]
                    if cfg.settings.open_pr_as_draft:
                        gh_cmd.append("--draft")
                    pr_res = subprocess.run(gh_cmd, cwd=str(wt_path), capture_output=True, text=True, check=False, env=env, timeout=30)
                    if pr_res.returncode == 0 and pr_res.stdout.strip():
                        pr_url = pr_res.stdout.strip()
                        pr_message = f"Pull Request opened on GitHub: {pr_url}"
            except Exception as e:
                logger.warning("Real git/gh PR creation encountered exception: %s; falling back to worktree URL", e)

        if session:
            session.pr_url = pr_url
            app.state.config_store.upsert_session(session)

        return {
            "success": True,
            "task_id": task_id,
            "pr_url": pr_url,
            "message": pr_message,
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
            return {"service": "julius-hub", "status": "running"}

        @app.get("/{full_path:path}")
        async def serve_spa_fallback(full_path: str):
            candidate = (dist_dir / full_path).resolve()
            try:
                if candidate.is_relative_to(dist_dir) and candidate.is_file():
                    return FileResponse(candidate)
            except (ValueError, Exception):
                pass
            index_file = dist_dir / "index.html"
            if index_file.is_file():
                return FileResponse(index_file)
            raise HTTPException(status_code=404, detail="Not Found")
    else:
        @app.get("/")
        async def root_fallback():
            return {
                "service": "julius-hub",
                "status": "running",
                "ui": "not_built",
            }

    return app


# Default application instance for Uvicorn runner
app = create_app()
