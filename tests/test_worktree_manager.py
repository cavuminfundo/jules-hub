"""
Unit tests for Julius Hub Worktree Manager (hub/worktree_manager.py).
Tests isolated worktree lifecycle, naming convention, test auto-detection,
process group timeout handling (killpg), and rollback on failure.
"""

import asyncio
import os
from pathlib import Path
import shutil
import stat
import subprocess
import pytest

from hub.models import WorktreeSessionInfo
from hub.worktree_manager import (
    WorktreeManager,
    WorktreeContext,
    detect_test_command,
    run_tests_async,
    run_cmd,
)


def _init_dummy_git_repo(repo_dir: Path) -> Path:
    """Initialize a bare-minimum git repository for worktree testing."""
    repo_dir.mkdir(parents=True, exist_ok=True)
    run_cmd(["git", "init", "-b", "main"], cwd=repo_dir)
    run_cmd(["git", "config", "user.email", "jules@hub.local"], cwd=repo_dir)
    run_cmd(["git", "config", "user.name", "Jules Tester"], cwd=repo_dir)

    readme = repo_dir / "README.md"
    readme.write_text("# Test Repo\n", encoding="utf-8")
    run_cmd(["git", "add", "README.md"], cwd=repo_dir)
    run_cmd(["git", "commit", "-m", "initial commit"], cwd=repo_dir)
    return repo_dir


def test_env_vars_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Verify environment variable overrides for worktrees dir and registry path."""
    custom_wt = tmp_path / "custom_worktrees"
    custom_reg = tmp_path / "custom_registry.json"

    monkeypatch.setenv("JULES_WORKTREES_DIR", str(custom_wt))
    monkeypatch.setenv("PROJECTS_REGISTRY_PATH", str(custom_reg))

    wm = WorktreeManager()
    assert wm.worktrees_dir == custom_wt.resolve()
    assert wm.registry_path == custom_reg.resolve()

    # Explicit constructor arguments override environment variables
    override_wt = tmp_path / "override_wt"
    override_reg = tmp_path / "override_reg.json"
    wm2 = WorktreeManager(worktrees_dir=override_wt, registry_path=override_reg)
    assert wm2.worktrees_dir == override_wt.resolve()
    assert wm2.registry_path == override_reg.resolve()


def test_naming_convention(tmp_path: Path):
    """Verify naming matches <repo>-<persona>-<timestamp_uuid>."""
    repo_dir = _init_dummy_git_repo(tmp_path / "demo_repo")
    wt_dir = tmp_path / "worktrees"
    wm = WorktreeManager(worktrees_dir=wt_dir)

    session = wm.create_session(repo_dir, persona="bolt")
    slug = session.worktree_path.name

    # Must start with repo name and persona
    assert slug.startswith("demo_repo-bolt-")
    # Must contain timestamp and uuid parts separated by underscore
    parts = slug.split("-")
    assert len(parts) >= 3
    assert session.branch.startswith("curator/bolt-")


def test_detect_test_command(tmp_path: Path):
    """Verify test runner auto-detection hierarchy."""
    # 1. Custom repo script: run_fast_tests.sh
    script_dir = tmp_path / "fast_script_repo"
    script_dir.mkdir()
    fast_script = script_dir / "run_fast_tests.sh"
    fast_script.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fast_script.chmod(fast_script.stat().st_mode | stat.S_IEXEC)
    assert detect_test_command(script_dir) == ["./run_fast_tests.sh"]

    # 2. Node.js package.json with test script
    node_dir = tmp_path / "node_repo"
    node_dir.mkdir()
    pkg_json = node_dir / "package.json"
    pkg_json.write_text('{"scripts": {"test": "jest"}}', encoding="utf-8")
    assert detect_test_command(node_dir) == ["npm", "test"]

    # With pnpm-lock
    (node_dir / "pnpm-lock.yaml").write_text("", encoding="utf-8")
    assert detect_test_command(node_dir) == ["pnpm", "test"]

    # 3. Python pytest
    py_dir = tmp_path / "python_repo"
    py_dir.mkdir()
    (py_dir / "pyproject.toml").write_text("[project]\nname='test'\n", encoding="utf-8")
    assert detect_test_command(py_dir) == ["uv", "run", "pytest", "-q", "--tb=short", "--maxfail=2"]

    # 4. Empty repo returns None
    empty_dir = tmp_path / "empty_repo"
    empty_dir.mkdir()
    assert detect_test_command(empty_dir) is None


def test_worktree_session_lifecycle_and_unpacking(tmp_path: Path):
    """Verify session creation, tuple unpacking, and worktree verification."""
    repo_dir = _init_dummy_git_repo(tmp_path / "lifecycle_repo")
    wt_dir = tmp_path / "worktrees"
    wm = WorktreeManager(worktrees_dir=wt_dir)

    with wm.create_session(repo_dir, persona="palette") as (worktree, branch):
        assert Path(worktree).exists()
        assert (Path(worktree) / "README.md").exists()
        assert branch.startswith("curator/palette-")

        # Verify active git branch
        res = run_cmd(["git", "branch", "--show-current"], cwd=worktree)
        assert res.stdout.strip() == branch


def test_auto_cleanup_on_exception(tmp_path: Path):
    """Verify that an exception inside WorktreeContext triggers auto-prune cleanup."""
    repo_dir = _init_dummy_git_repo(tmp_path / "fail_repo")
    wt_dir = tmp_path / "worktrees"
    wm = WorktreeManager(worktrees_dir=wt_dir)

    target_path = None
    with pytest.raises(RuntimeError, match="Simulated error"):
        with wm.create_session(repo_dir, persona="sentinel") as ctx:
            target_path = ctx.worktree_path
            assert target_path.exists()
            raise RuntimeError("Simulated error")

    assert target_path is not None
    assert not target_path.exists(), "Worktree directory should have been removed on exception"


def test_auto_cleanup_on_abort(tmp_path: Path):
    """Verify that calling ctx.abort() removes worktree cleanly."""
    repo_dir = _init_dummy_git_repo(tmp_path / "abort_repo")
    wt_dir = tmp_path / "worktrees"
    wm = WorktreeManager(worktrees_dir=wt_dir)

    with wm.create_session(repo_dir, persona="bolt") as ctx:
        target_path = ctx.worktree_path
        assert target_path.exists()
        ctx.abort()
        assert not target_path.exists()


@pytest.mark.asyncio
async def test_run_tests_async_no_tests(tmp_path: Path):
    """Verify test run when no automated tests exist in repo."""
    empty_repo = tmp_path / "no_tests"
    empty_repo.mkdir()
    passed, msg = await run_tests_async(empty_repo)
    assert passed is True
    assert "No automated test suite detected" in msg


@pytest.mark.asyncio
async def test_run_tests_async_success_and_failure(tmp_path: Path):
    """Verify test execution with passing and failing test commands."""
    repo_dir = tmp_path / "fast_repo"
    repo_dir.mkdir()
    script = repo_dir / "run_fast_tests.sh"

    # Passing test
    script.write_text("#!/bin/sh\necho 'FAST GREEN'\nexit 0\n", encoding="utf-8")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    passed, output = await run_tests_async(repo_dir, timeout_seconds=10)
    assert passed is True
    assert "FAST GREEN" in output

    # Failing test
    script.write_text("#!/bin/sh\necho 'FAST RED'\nexit 1\n", encoding="utf-8")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    passed, output = await run_tests_async(repo_dir, timeout_seconds=10)
    assert passed is False
    assert "FAST RED" in output


@pytest.mark.asyncio
async def test_run_tests_async_timeout_killpg(tmp_path: Path):
    """Verify process group termination upon timeout."""
    repo_dir = tmp_path / "hang_repo"
    repo_dir.mkdir()
    script = repo_dir / "run_fast_tests.sh"
    # Sleep longer than the 1s timeout
    script.write_text("#!/bin/sh\nsleep 10\nexit 0\n", encoding="utf-8")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)

    passed, output = await run_tests_async(repo_dir, timeout_seconds=1)
    assert passed is False
    assert "Test timeout exceeded (1s)" in output


def test_list_worktrees_and_cleanup_all(tmp_path: Path):
    """Verify list_worktrees and cleanup_all functions."""
    repo_dir = _init_dummy_git_repo(tmp_path / "repo_for_list")
    wt_dir = tmp_path / "worktrees_listing"
    wm = WorktreeManager(worktrees_dir=wt_dir)

    session = wm.create_session(repo_dir, persona="bolt")
    with session as ctx:
        ctx.mark_success()
        active_list = wm.list_worktrees()
        assert len(active_list) == 1
        assert active_list[0].repo_name == "repo_for_list"
        assert active_list[0].persona == "bolt"
        assert active_list[0].is_active is True

    # Now cleanup all
    wm.cleanup_all()
    assert len(wm.list_worktrees()) == 0
