"""
Jules Hub Worktree Manager: Isolated git worktree lifecycle and test execution.
Spawns 100% isolated git worktrees with unique timestamp/UUID naming, detects project test runners,
enforces 120s test timeouts with process group kill (killpg), and automatically rolls back/prunes on abort.

All subprocess executions use typed argument lists (list[str]) with shell=False.
"""

import asyncio
import datetime
import json
import logging
import os
from pathlib import Path
import shutil
import signal
import subprocess
from typing import Any, Dict, List, Optional, Tuple, Union
import uuid

from hub.models import WorktreeSessionInfo

logger = logging.getLogger("hub.worktree_manager")

DEFAULT_WORKTREES_DIR = Path("/home/federico/jules/worktrees")
DEFAULT_REGISTRY_PATH = Path("/home/federico/.gemini/config/projects_registry.json")


def run_cmd(
    cmd: List[str],
    cwd: Optional[Union[str, Path]] = None,
    check: bool = True,
    input_str: Optional[str] = None,
    timeout: Optional[float] = None,
) -> subprocess.CompletedProcess:
    """
    Execute subprocess command safely with typed list[str] arguments and shell=False.
    Guarantees immunity against command injection.
    """
    if not isinstance(cmd, list) or not all(isinstance(arg, str) for arg in cmd):
        raise TypeError(f"Command must be a list of strings, got: {type(cmd)}")

    resolved_cwd = str(cwd) if cwd is not None else None
    result = subprocess.run(
        cmd,
        cwd=resolved_cwd,
        input=input_str,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        shell=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(cmd)}\n"
            f"Stdout: {result.stdout.strip()}\n"
            f"Stderr: {result.stderr.strip()}"
        )
    return result


def detect_test_command(worktree_path: Union[str, Path]) -> Optional[List[str]]:
    """
    Autodetect the fastest local test command for the repository.
    1. Custom repo script: run_fast_tests.sh
    2. Node / Next.js: package.json (test or typecheck script)
    3. Python pytest: pyproject.toml, pytest.ini, or tests/ directory
    """
    wt = Path(worktree_path).resolve()

    # 1. Custom repo fast-test script
    fast_tests = wt / "run_fast_tests.sh"
    if fast_tests.exists() and os.access(fast_tests, os.X_OK):
        return ["./run_fast_tests.sh"]

    # 2. Node / TypeScript / Next.js
    pkg_json = wt / "package.json"
    if pkg_json.exists():
        try:
            with open(pkg_json, "r", encoding="utf-8") as f:
                pkg_data = json.load(f)
            scripts = pkg_data.get("scripts", {})
            if "test" in scripts:
                return ["pnpm", "test"] if (wt / "pnpm-lock.yaml").exists() else ["npm", "test"]
            if "typecheck" in scripts:
                return ["npm", "run", "typecheck"]
        except Exception as e:
            logger.debug("Error parsing %s: %s", pkg_json, e)

    # 3. Python pytest
    has_pyproject = (wt / "pyproject.toml").exists()
    has_pytest_ini = (wt / "pytest.ini").exists()
    has_tests_dir = (wt / "tests").is_dir()
    if has_pyproject or has_pytest_ini or has_tests_dir:
        venv_pytest = wt / ".venv" / "bin" / "pytest"
        if venv_pytest.exists() and os.access(venv_pytest, os.X_OK):
            return [str(venv_pytest), "-q", "--tb=short", "--maxfail=2"]
        return ["uv", "run", "pytest", "-q", "--tb=short", "--maxfail=2"]

    return None


async def run_tests_async(
    worktree_path: Union[str, Path],
    timeout_seconds: int = 120,
) -> Tuple[bool, str]:
    """
    Execute tests asynchronously inside a worktree with a process group kill (killpg)
    upon reaching timeout_seconds (default 120s). Returns (success, output).
    Uses typed argument list with shell=False.
    """
    wt = Path(worktree_path).resolve()
    test_cmd = detect_test_command(wt)
    if not test_cmd:
        return True, "No automated test suite detected. Skipping test gate."

    logger.info("Executing test suite in worktree '%s': %s", wt, " ".join(test_cmd))

    proc = None
    try:
        proc = await asyncio.create_subprocess_exec(
            *test_cmd,
            cwd=str(wt),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            preexec_fn=os.setsid,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=float(timeout_seconds),
        )
        output = (
            stdout.decode("utf-8", errors="replace") + "\n" + stderr.decode("utf-8", errors="replace")
        ).strip()
        return (proc.returncode == 0, output)

    except asyncio.TimeoutError:
        logger.warning("Test run exceeded timeout of %ds in %s; killing process group", timeout_seconds, wt)
        if proc is not None and proc.pid:
            try:
                pgid = os.getpgid(proc.pid)
                os.killpg(pgid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except Exception as e:
                logger.error("Failed to kill process group for pid %s: %s", proc.pid, e)
            try:
                await asyncio.wait_for(proc.wait(), timeout=2.0)
            except Exception:
                pass
        return False, f"Test timeout exceeded ({timeout_seconds}s)"

    except Exception as e:
        logger.error("Exception during test execution in %s: %s", wt, e)
        if proc is not None and proc.pid:
            try:
                pgid = os.getpgid(proc.pid)
                os.killpg(pgid, signal.SIGKILL)
            except Exception:
                pass
        return False, f"Error executing test suite: {e}"


class WorktreeContext:
    """
    Context manager for an isolated git worktree.
    Supports both synchronous ('with') and asynchronous ('async with') contexts.
    Automatically executes git worktree remove --force and git worktree prune on failure/abort.
    """

    def __init__(
        self,
        repo_path: Path,
        worktree_path: Path,
        branch: str,
        persona: str,
        manager: "WorktreeManager",
        auto_cleanup: bool = False,
    ):
        self.repo_path = repo_path
        self.worktree_path = worktree_path
        self.branch = branch
        self.persona = persona
        self.manager = manager
        self.auto_cleanup = auto_cleanup
        self.success: bool = False
        self.aborted: bool = False
        self.active: bool = False

    def __enter__(self) -> "WorktreeContext":
        self.manager.worktrees_dir.mkdir(parents=True, exist_ok=True)

        # Prune dead worktrees from repo
        run_cmd(["git", "worktree", "prune"], cwd=self.repo_path, check=False)

        # If previous worktree at this exact destination exists, remove it cleanly
        if self.worktree_path.exists():
            run_cmd(
                ["git", "worktree", "remove", "--force", str(self.worktree_path)],
                cwd=self.repo_path,
                check=False,
            )
            shutil.rmtree(self.worktree_path, ignore_errors=True)

        # Check if target branch exists locally or on remote
        branch_check = run_cmd(
            ["git", "show-ref", "--verify", f"refs/heads/{self.branch}"],
            cwd=self.repo_path,
            check=False,
        )
        if branch_check.returncode == 0:
            run_cmd(["git", "worktree", "add", str(self.worktree_path), self.branch], cwd=self.repo_path)
        else:
            remote_check = run_cmd(
                ["git", "show-ref", "--verify", f"refs/remotes/origin/{self.branch}"],
                cwd=self.repo_path,
                check=False,
            )
            if remote_check.returncode == 0:
                run_cmd(
                    ["git", "worktree", "add", "-b", self.branch, str(self.worktree_path), f"origin/{self.branch}"],
                    cwd=self.repo_path,
                )
            else:
                run_cmd(
                    ["git", "worktree", "add", "-b", self.branch, str(self.worktree_path), "HEAD"],
                    cwd=self.repo_path,
                )

        # Symlink large shared dependencies from parent repo into worktree if present
        for dep_name in [".venv", "node_modules", ".env"]:
            parent_dep = self.repo_path / dep_name
            target_dep = self.worktree_path / dep_name
            if parent_dep.exists() and not target_dep.exists():
                try:
                    os.symlink(parent_dep, target_dep)
                except Exception as e:
                    logger.debug("Could not symlink %s into worktree: %s", dep_name, e)

        self.active = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Auto-prune on unhandled exception, explicit abort, or if auto_cleanup is True
        if exc_type is not None or self.aborted or self.auto_cleanup:
            self.cleanup()
        self.active = False
        return False

    async def __aenter__(self) -> "WorktreeContext":
        return await asyncio.to_thread(self.__enter__)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await asyncio.to_thread(self.__exit__, exc_type, exc_val, exc_tb)

    def abort(self) -> None:
        """Mark session as aborted and clean up immediately."""
        self.aborted = True
        self.cleanup()

    def mark_success(self) -> None:
        """Mark session as successfully completed."""
        self.success = True

    def cleanup(self) -> None:
        """Forcefully remove worktree and prune dangling locks."""
        try:
            if self.worktree_path.exists():
                run_cmd(
                    ["git", "worktree", "remove", "--force", str(self.worktree_path)],
                    cwd=self.repo_path,
                    check=False,
                )
                if self.worktree_path.exists():
                    shutil.rmtree(self.worktree_path, ignore_errors=True)
            run_cmd(["git", "worktree", "prune"], cwd=self.repo_path, check=False)
        except Exception as e:
            logger.warning("Error cleaning up worktree at %s: %s", self.worktree_path, e)

    def __iter__(self):
        """Allow tuple unpacking: (worktree_path, branch) = ctx."""
        yield self.worktree_path
        yield self.branch


class WorktreeManager:
    """
    Manages isolated git worktrees across registered repositories.
    Supports environment variable overrides:
    - JULES_WORKTREES_DIR
    - PROJECTS_REGISTRY_PATH
    """

    def __init__(
        self,
        worktrees_dir: Optional[Union[str, Path]] = None,
        registry_path: Optional[Union[str, Path]] = None,
    ):
        env_worktrees = os.environ.get("JULES_WORKTREES_DIR")
        if worktrees_dir is not None:
            self.worktrees_dir = Path(worktrees_dir).expanduser().resolve()
        elif env_worktrees:
            self.worktrees_dir = Path(env_worktrees).expanduser().resolve()
        else:
            self.worktrees_dir = DEFAULT_WORKTREES_DIR.resolve()

        env_registry = os.environ.get("PROJECTS_REGISTRY_PATH")
        if registry_path is not None:
            self.registry_path = Path(registry_path).expanduser().resolve()
        elif env_registry:
            self.registry_path = Path(env_registry).expanduser().resolve()
        else:
            self.registry_path = DEFAULT_REGISTRY_PATH.resolve()

    def resolve_repo_path(self, repo_query: Union[str, Path]) -> Path:
        """Resolve project name or path against projects_registry.json or direct path."""
        direct_path = Path(repo_query).expanduser().resolve()
        if direct_path.exists() and (direct_path / ".git").exists():
            return direct_path

        if self.registry_path.exists():
            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                projects = data.get("projects", []) if isinstance(data, dict) else data
                query_lower = str(repo_query).lower()
                for p in projects:
                    name = p.get("name", "").lower()
                    p_path = Path(p.get("path", "")).expanduser().resolve()
                    if name == query_lower or p_path.name.lower() == query_lower:
                        if p_path.exists() and (p_path / ".git").exists():
                            return p_path
            except Exception as e:
                logger.warning("Error reading registry %s: %s", self.registry_path, e)

        raise ValueError(f"Could not resolve '{repo_query}' to an existing git repository.")

    def list_registered_projects(self) -> List[Dict[str, Any]]:
        """Return all valid git repositories registered in projects_registry.json."""
        results = []
        if not self.registry_path.exists():
            return results

        try:
            with open(self.registry_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            projects = data.get("projects", []) if isinstance(data, dict) else data
            for p in projects:
                p_path = Path(p.get("path", "")).expanduser().resolve()
                if p_path.exists() and (p_path / ".git").exists():
                    results.append({
                        "name": p.get("name", p_path.name),
                        "path": str(p_path),
                        "description": (p.get("description") or "")[:80],
                    })
        except Exception as e:
            logger.warning("Error parsing projects from registry: %s", e)
        return results

    def create_session(
        self,
        repo_name_or_path: Union[str, Path],
        persona: str = "bolt",
        branch_name: Optional[str] = None,
        auto_cleanup: bool = False,
    ) -> WorktreeContext:
        """
        Create a new isolated git worktree context with naming:
        worktrees/<repo>-<persona>-<timestamp_uuid>
        """
        repo_path = self.resolve_repo_path(repo_name_or_path)
        timestamp_uuid = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        slug = f"{repo_path.name}-{persona}-{timestamp_uuid}"
        branch = branch_name or f"curator/{persona}-{timestamp_uuid}"
        worktree_path = self.worktrees_dir / slug

        return WorktreeContext(
            repo_path=repo_path,
            worktree_path=worktree_path,
            branch=branch,
            persona=persona,
            manager=self,
            auto_cleanup=auto_cleanup,
        )

    async def run_tests_async(
        self,
        worktree_path: Union[str, Path],
        timeout_seconds: int = 120,
    ) -> Tuple[bool, str]:
        """Delegate to run_tests_async helper."""
        return await run_tests_async(worktree_path, timeout_seconds=timeout_seconds)

    def list_worktrees(self) -> List[WorktreeSessionInfo]:
        """List active worktrees currently in worktrees_dir."""
        results: List[WorktreeSessionInfo] = []
        if not self.worktrees_dir.exists():
            return results

        for item in self.worktrees_dir.iterdir():
            if item.is_dir() and (item / ".git").exists():
                res = run_cmd(["git", "branch", "--show-current"], cwd=item, check=False)
                branch = res.stdout.strip() or "detached"
                parts = item.name.split("-")
                repo_name = parts[0] if len(parts) > 0 else "unknown"
                persona = parts[1] if len(parts) > 1 else "curator"
                created_iso = datetime.datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                results.append(
                    WorktreeSessionInfo(
                        worktree_path=str(item),
                        branch=branch,
                        repo_name=repo_name,
                        persona=persona,
                        created_at=created_iso,
                        is_active=True,
                    )
                )
        return results

    def prune_worktree(self, worktree_path: Union[str, Path], force: bool = True) -> bool:
        """Prune and remove a specific worktree by path."""
        target = Path(worktree_path).resolve()
        if not target.exists():
            return False

        # Attempt to identify owning repo from registered projects
        cleaned = False
        for proj in self.list_registered_projects():
            repo_path = Path(proj["path"])
            try:
                cmd = ["git", "worktree", "remove"]
                if force:
                    cmd.append("--force")
                cmd.append(str(target))
                res = run_cmd(cmd, cwd=repo_path, check=False)
                if res.returncode == 0:
                    run_cmd(["git", "worktree", "prune"], cwd=repo_path, check=False)
                    cleaned = True
                    break
            except Exception:
                pass

        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
            cleaned = True

        return cleaned

    def cleanup_all(self) -> None:
        """Remove and prune all worktrees in worktrees_dir across all registered repos."""
        if not self.worktrees_dir.exists():
            return

        for item in self.worktrees_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)

        for proj in self.list_registered_projects():
            p_path = Path(proj["path"])
            run_cmd(["git", "worktree", "prune"], cwd=p_path, check=False)


def cleanup_all(manager: Optional[WorktreeManager] = None) -> None:
    """Module-level cleanup helper."""
    mgr = manager or WorktreeManager()
    mgr.cleanup_all()
