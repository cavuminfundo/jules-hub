"""
Background scheduler for autonomous repository curation.
Periodically scans enabled repositories according to configured interval hours,
enforces max_pending_worktrees guardrails, and schedules curation tasks without automatic PR creation.
"""

import asyncio
from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Dict, Optional

from hub.config_store import ConfigStore
from hub.models import HubConfig, RepoScheduleConfig
from hub.scanner import find_suggestions

logger = logging.getLogger("hub.scheduler")


class BackgroundScheduler:
    """
    Background asyncio daemon checking repository schedules periodically.
    Enforces max_pending_worktrees safety limits before launching autonomous curation.
    Never creates automatic Pull Requests.
    """

    def __init__(
        self,
        config_store: ConfigStore,
        worktree_manager: Optional[Any] = None,
        engine_router: Optional[Any] = None,
    ):
        self.config_store = config_store
        self.worktree_manager = worktree_manager
        self.engine_router = engine_router
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start background scheduling loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("BackgroundScheduler started.")

    async def stop(self) -> None:
        """Stop background scheduling loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("BackgroundScheduler stopped.")

    async def trigger_repo(self, repo_name: str) -> Dict[str, Any]:
        """
        Trigger curation cycle for a repository.
        Scans for real candidates via find_suggestions, updates schedule timestamps,
        and enforces max_pending_worktrees limit.
        """
        cfg = self.config_store.load_config()
        target_sched = next((s for s in cfg.repo_schedules if s.repo_name == repo_name), None)
        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat()

        if target_sched:
            target_sched.last_run_at = now_iso
            target_sched.next_run_at = (now_dt + timedelta(hours=target_sched.interval_hours)).isoformat()
            self.config_store.save_config(cfg)

        # Enforce max_pending_worktrees safety limit
        if self.worktree_manager and target_sched:
            try:
                active_worktrees = [
                    w for w in self.worktree_manager.list_worktrees()
                    if getattr(w, "repo_name", None) == repo_name and getattr(w, "is_active", True)
                ]
                if len(active_worktrees) >= target_sched.max_pending_worktrees:
                    logger.warning(
                        "Max pending worktrees reached for %s (%d >= %d). Trigger recorded without new worktree.",
                        repo_name,
                        len(active_worktrees),
                        target_sched.max_pending_worktrees,
                    )
                    return {
                        "repo_name": repo_name,
                        "triggered": True,
                        "triggered_at": now_iso,
                        "last_triggered_at": now_iso,
                        "status": "capped_pending_worktrees",
                        "active_worktrees": len(active_worktrees),
                    }
            except Exception as e:
                logger.error("Error inspecting active worktrees for %s: %s", repo_name, e)

        # Scan for real suggestions
        suggestions_count = 0
        if self.worktree_manager:
            try:
                repo_path = self.worktree_manager.resolve_repo_path(repo_name)
                state = self.config_store.load_state()
                suggs = find_suggestions(repo_path, ignored_ids=set(state.ignored_suggestions))
                suggestions_count = len(suggs)
            except Exception as e:
                logger.debug("find_suggestions scan during trigger_repo for %s: %s", repo_name, e)

        return {
            "repo_name": repo_name,
            "triggered": True,
            "triggered_at": now_iso,
            "last_triggered_at": now_iso,
            "status": "scheduled",
            "suggestions_count": suggestions_count,
        }

    async def _tick(self) -> None:
        """Evaluate due repository schedules and trigger curation."""
        cfg = self.config_store.load_config()
        now = datetime.now(timezone.utc)
        for sched in cfg.repo_schedules:
            if not sched.enabled:
                continue
            due = True
            if sched.last_run_at:
                try:
                    last_dt = datetime.fromisoformat(sched.last_run_at)
                    if now < last_dt + timedelta(hours=sched.interval_hours):
                        due = False
                except Exception:
                    pass
            if due:
                logger.info("Repository '%s' is due for curation run", sched.repo_name)
                await self.trigger_repo(sched.repo_name)

    async def _loop(self) -> None:
        """Continuous scheduler evaluation loop running every 60 seconds."""
        while self._running:
            try:
                await self._tick()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("Error in BackgroundScheduler tick: %s", e)
            try:
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
