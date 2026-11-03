"""
Unit tests for Julius Hub FastAPI Server (hub/app.py).
Tests REST endpoints (/api/health, /api/projects, /api/suggestions, /api/run,
/api/escalate, /api/worktrees, /api/worktrees/prune), SSE stream (/api/stream/{task_id}),
CORS, and conditional static UI mounting with SPA fallback.
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from hub.app import create_app
from hub.cdp_bridge import CDPBridge, CDPResponse
from hub.engine_router import EngineRouter
from hub.models import (
    EngineMode,
    EscalateRequest,
    PatchResult,
    RunRequest,
    Suggestion,
    TaskStatus,
    WorktreeSessionInfo,
)
from hub.worktree_manager import WorktreeManager


@pytest.fixture
def mock_worktree_manager(tmp_path: Path):
    wm = MagicMock(spec=WorktreeManager)
    wm.worktrees_dir = tmp_path / "worktrees"
    wm.registry_path = tmp_path / "registry.json"

    # Default mocks
    wm.list_registered_projects.return_value = [
        {"name": "test-repo", "path": str(tmp_path / "test-repo"), "description": "Test Repo"}
    ]
    wm.resolve_repo_path.return_value = tmp_path / "test-repo"
    wm.list_worktrees.return_value = [
        WorktreeSessionInfo(
            worktree_path=str(tmp_path / "worktrees" / "test-bolt-1"),
            branch="curator/bolt-1",
            repo_name="test-repo",
            persona="bolt",
            created_at="2026-10-31T15:00:00",
            is_active=True,
        )
    ]
    wm.prune_worktree.return_value = True
    wm.cleanup_all.return_value = None
    wm.run_tests_async = AsyncMock(return_value=(True, "All tests passed"))
    return wm


@pytest.fixture
def mock_engine_router():
    router = MagicMock(spec=EngineRouter)
    router.analyze_and_patch = AsyncMock(
        return_value=PatchResult(
            success=True,
            diff="--- a/file.py\n+++ b/file.py\n@@ -1 +1 @@\n-# old\n+# new",
            lines_changed=2,
            engine_used="antigravity_flash",
        )
    )
    return router


@pytest.fixture
def mock_cdp_bridge():
    bridge = MagicMock(spec=CDPBridge)
    bridge.escalate_to_antigravity = AsyncMock(
        return_value=CDPResponse(
            success=True,
            message="Escalated to Antigravity Desktop successfully",
            response_data={"id": 1, "result": "ok"},
        )
    )
    return bridge


@pytest.fixture
def client(mock_worktree_manager, mock_engine_router, mock_cdp_bridge, tmp_path):
    # App created with a non-existent UI dist path to test default API mode
    app = create_app(
        worktree_manager=mock_worktree_manager,
        engine_router=mock_engine_router,
        cdp_bridge=mock_cdp_bridge,
        ui_dist_path=tmp_path / "nonexistent_dist",
    )
    return TestClient(app)


def test_api_health(client):
    """Verify /api/health endpoint returns 200 and healthy status."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "julius-hub"
    assert "version" in data


def test_api_projects(client, mock_worktree_manager):
    """Verify /api/projects returns registered projects list."""
    resp = client.get("/api/projects")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "test-repo"
    assert mock_worktree_manager.list_registered_projects.called


def test_api_suggestions_default(client):
    """Verify /api/suggestions returns suggestions list."""
    sample_suggestions = [
        Suggestion(
            id="bolt-1",
            persona="bolt",
            category="performance",
            title="Add cache decorator",
            file="service.py",
            line=42,
            issue="Repeated calculations",
            impact="Reduces CPU load",
            code_snippet="@lru_cache\ndef compute(): pass",
        )
    ]

    with patch("hub.app.find_suggestions", return_value=sample_suggestions):
        resp = client.get("/api/suggestions")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == "bolt-1"
        assert data[0]["persona"] == "bolt"


def test_api_suggestions_with_filters(client):
    """Verify /api/suggestions filters by mode and category."""
    with patch("hub.app.find_suggestions", return_value=[]) as mock_find:
        resp = client.get("/api/suggestions?repo=test-repo&mode=sentinel&category=security")
        assert resp.status_code == 200
        assert mock_find.called
        kwargs = mock_find.call_args[1]
        assert kwargs["mode"] == "sentinel"
        assert kwargs["category"] == "security"


def test_api_worktrees(client, mock_worktree_manager):
    """Verify /api/worktrees returns active worktree sessions."""
    resp = client.get("/api/worktrees")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["repo_name"] == "test-repo"
    assert data[0]["persona"] == "bolt"
    assert data[0]["is_active"] is True


def test_api_worktrees_prune_all(client, mock_worktree_manager):
    """Verify /api/worktrees/prune prunes all worktrees when no path is provided."""
    resp = client.post("/api/worktrees/prune", json={})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "All worktrees pruned" in data["message"]
    assert mock_worktree_manager.cleanup_all.called


def test_api_worktrees_prune_specific(client, mock_worktree_manager):
    """Verify /api/worktrees/prune prunes a specific worktree path."""
    resp = client.post("/api/worktrees/prune", json={"worktree_path": "/path/to/wt", "force": True})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    mock_worktree_manager.prune_worktree.assert_called_with("/path/to/wt", True)


def test_api_escalate_success(client, mock_cdp_bridge):
    """Verify /api/escalate invokes CDPBridge and returns 200."""
    payload = {
        "repo": "jules-hub",
        "worktree_path": "/workspaces/worktrees/wt-1",
        "branch": "curator/bolt-1",
        "diff_summary": "Fix async loop",
        "test_status": "PASSED",
        "instruction": "Senior review requested",
    }
    resp = client.post("/api/escalate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "Escalated" in data["message"]
    assert mock_cdp_bridge.escalate_to_antigravity.called


def test_api_escalate_port_closed_resilience(client, mock_cdp_bridge):
    """Verify /api/escalate does NOT raise HTTP 500 when CDP port is unreachable."""
    mock_cdp_bridge.escalate_to_antigravity.return_value = CDPResponse(
        success=False,
        message="CDP connection refused on 127.0.0.1:9000",
        error="CDP connection refused on 127.0.0.1:9000",
    )
    payload = {
        "repo": "jules-hub",
        "worktree_path": "/workspaces/worktrees/wt-1",
        "branch": "curator/bolt-1",
        "diff_summary": "Fix async loop",
        "test_status": "PASSED",
    }
    resp = client.post("/api/escalate", json=payload)
    assert resp.status_code == 200  # Must be 200 with success=False, not 500
    data = resp.json()
    assert data["success"] is False
    assert "connection refused" in data["message"].lower()


def test_api_run_dry_run(client):
    """Verify /api/run in dry_run mode completes immediately."""
    payload = {
        "repo": "test-repo",
        "persona": "bolt",
        "dry_run": True,
    }
    resp = client.post("/api/run", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "passed"
    assert "dry run" in data["message"].lower()
    assert "task_" in data["task_id"]


def test_api_run_success_flow(client, mock_worktree_manager, mock_engine_router, tmp_path):
    """Verify /api/run executes patch, runs tests, and completes successfully."""
    wt_mock_path = tmp_path / "mock_wt"
    wt_mock_path.mkdir(parents=True, exist_ok=True)

    class MockContext:
        def __init__(self):
            self.worktree_path = wt_mock_path
            self.branch = "curator/bolt-123"

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        def mark_success(self):
            pass

    mock_worktree_manager.create_session.return_value = MockContext()

    payload = {
        "repo": "test-repo",
        "persona": "bolt",
        "target_file": "app.py",
        "issue_context": "Optimize caching",
        "mode": "antigravity_flash",
        "dry_run": False,
    }
    resp = client.post("/api/run", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "passed"
    assert "task_" in data["task_id"]


def test_api_run_test_failure_escalation(client, mock_worktree_manager, tmp_path):
    """Verify /api/run flags for senior review when tests fail."""
    wt_mock_path = tmp_path / "mock_wt_fail"
    wt_mock_path.mkdir(parents=True, exist_ok=True)

    class MockContext:
        def __init__(self):
            self.worktree_path = wt_mock_path
            self.branch = "curator/bolt-fail"

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        def mark_success(self):
            pass

    mock_worktree_manager.create_session.return_value = MockContext()
    mock_worktree_manager.run_tests_async = AsyncMock(return_value=(False, "AssertionError in test_main"))

    payload = {
        "repo": "test-repo",
        "persona": "bolt",
        "dry_run": False,
    }
    resp = client.post("/api/run", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "needs_escalation"


def test_api_run_background(client):
    """Verify /api/run with background=true schedules background task."""
    payload = {
        "repo": "test-repo",
        "persona": "bolt",
        "dry_run": True,
    }
    resp = client.post("/api/run?background=true", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "running"
    assert "background" in data["message"].lower()


def test_api_stream_logs(client):
    """Verify /api/stream/{task_id} SSE streaming of task execution logs."""
    # First run a dry-run task to populate logs
    run_resp = client.post("/api/run", json={"repo": "test-repo", "persona": "bolt", "dry_run": True})
    task_id = run_resp.json()["task_id"]

    # Stream logs
    stream_resp = client.get(f"/api/stream/{task_id}")
    assert stream_resp.status_code == 200
    assert "text/event-stream" in stream_resp.headers["content-type"]
    text = stream_resp.text
    assert "data:" in text
    assert "Dry-run enabled" in text
    assert "done" in text


def test_api_stream_not_found(client):
    """Verify /api/stream/{task_id} returns 404 for unknown task."""
    resp = client.get("/api/stream/nonexistent_task_999")
    assert resp.status_code == 404


def test_conditional_ui_mount_not_built(tmp_path):
    """Verify GET / returns JSON status when UI is not built."""
    app = create_app(ui_dist_path=tmp_path / "nonexistent")
    test_client = TestClient(app)

    resp = test_client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ui"] == "not_built"
    assert data["service"] == "julius-hub"


def test_conditional_ui_mount_built(tmp_path):
    """Verify GET / serves index.html and SPA fallback when ui/dist exists."""
    dist_dir = tmp_path / "ui_dist"
    dist_dir.mkdir(parents=True)
    assets_dir = dist_dir / "assets"
    assets_dir.mkdir()

    index_html = dist_dir / "index.html"
    index_html.write_text("<!DOCTYPE html><html><body>Jules Hub UI</body></html>", encoding="utf-8")

    asset_file = assets_dir / "bundle.js"
    asset_file.write_text("console.log('ui bundle');", encoding="utf-8")

    app = create_app(ui_dist_path=dist_dir)
    test_client = TestClient(app)

    # Root route serves index.html
    resp_root = test_client.get("/")
    assert resp_root.status_code == 200
    assert "Jules Hub UI" in resp_root.text

    # Static asset route serves bundle.js
    resp_asset = test_client.get("/assets/bundle.js")
    assert resp_asset.status_code == 200
    assert "ui bundle" in resp_asset.text

    # SPA route fallback serves index.html
    resp_spa = test_client.get("/settings/advanced")
    assert resp_spa.status_code == 200
    assert "Jules Hub UI" in resp_spa.text

    # API endpoints take precedence and are not caught by SPA fallback
    resp_health = test_client.get("/api/health")
    assert resp_health.status_code == 200
    assert resp_health.json()["status"] == "ok"


def test_cors_middleware(client):
    """Verify CORS headers are returned on preflight requests."""
    resp = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") in ("*", "http://localhost:5173")


def test_api_sessions_and_tasks(client, tmp_path):
    """Verify /api/sessions and /api/tasks/{task_id} endpoints."""
    # 1. Run dry_run task to create a session record
    run_resp = client.post("/api/run", json={"repo": "test-repo", "persona": "bolt", "dry_run": True})
    assert run_resp.status_code == 200
    task_id = run_resp.json()["task_id"]

    # 2. Get sessions list
    sessions_resp = client.get("/api/sessions")
    assert sessions_resp.status_code == 200
    sessions = sessions_resp.json()
    assert len(sessions) >= 1
    assert any(s["task_id"] == task_id for s in sessions)

    # Filter by repo
    repo_sessions_resp = client.get("/api/sessions?repo=test-repo")
    assert repo_sessions_resp.status_code == 200
    assert all(s["repo"] == "test-repo" for s in repo_sessions_resp.json())

    # 3. Get task detail
    detail_resp = client.get(f"/api/tasks/{task_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["task_id"] == task_id
    assert detail["session"] is not None
    assert detail["session"]["status"] == "passed"

    # 4. Unknown task returns 404
    nf_resp = client.get("/api/tasks/nonexistent_task_xyz")
    assert nf_resp.status_code == 404


def test_api_settings_secrets_and_config(client):
    """Verify /api/settings/secrets updates tokens and masks them in /api/config."""
    secrets_payload = {
        "github_token": "ghp_securetoken99999",
        "gemini_api_key": "AIzaSy_fake_api_key_888",
    }
    sec_resp = client.post("/api/settings/secrets", json=secrets_payload)
    assert sec_resp.status_code == 200
    sec_data = sec_resp.json()
    assert sec_data["has_github_token"] is True
    assert sec_data["github_token_masked"] == "ghp_...9999"
    assert sec_data["has_cloud_api_key"] is True
    assert "AIza..._888" in sec_data["cloud_api_key_masked"]

    # Verify GET /api/config does not expose plaintext secrets
    cfg_resp = client.get("/api/config")
    assert cfg_resp.status_code == 200
    cfg_json = cfg_resp.text
    assert "ghp_securetoken99999" not in cfg_json
    assert "AIzaSy_fake_api_key_888" not in cfg_json


def test_api_freeform_prompt_run(client, mock_worktree_manager, mock_engine_router, tmp_path):
    """Verify free-form prompt execution without target_file."""
    wt_mock_path = tmp_path / "mock_wt_freeform"
    wt_mock_path.mkdir(parents=True, exist_ok=True)

    class MockContext:
        def __init__(self):
            self.worktree_path = wt_mock_path
            self.branch = "curator/bolt-freeform"

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        def mark_success(self):
            pass

    mock_worktree_manager.create_session.return_value = MockContext()
    mock_engine_router.run_freeform_prompt = AsyncMock(
        return_value=PatchResult(
            success=True,
            diff="--- a/free.py\n+++ b/free.py\n@@ -1 +1 @@\n-# fix",
            lines_changed=1,
            engine_used="antigravity_flash",
        )
    )

    payload = {
        "repo": "test-repo",
        "persona": "bolt",
        "prompt": "Fix unused import in free.py",
        "dry_run": False,
    }
    resp = client.post("/api/run", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "passed"
    assert data["diff"] is not None
    assert "-# fix" in data["diff"]


def test_spa_path_traversal_guard(tmp_path):
    """Verify serve_spa_fallback rejects path traversal attempts."""
    dist_dir = tmp_path / "ui_dist_sec"
    dist_dir.mkdir(parents=True)
    index_html = dist_dir / "index.html"
    index_html.write_text("<html>App</html>", encoding="utf-8")

    app = create_app(ui_dist_path=dist_dir)
    test_client = TestClient(app)

    # Path traversal attempt should not read files outside dist_dir
    resp = test_client.get("/../../etc/passwd")
    # Should either serve index.html or 404, never 500 or file outside
    assert resp.status_code in (200, 404)
    assert "root:x:" not in resp.text

