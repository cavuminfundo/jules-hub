"""
Comprehensive unit tests for:
- probe_ollama_instance and CDPBridge (model discovery & escalation)
- EngineRouter.run_senior_review (scope ceiling & security gates)
- BackgroundScheduler (trigger, safety caps, start/stop lifecycle)
- Scanner ignored_ids filtering
- REST API endpoints (/api/config, /api/ollama/*, /api/cdp/models,
  /api/suggestions/.../discard, /api/tasks/.../senior-review,
  /api/tasks/.../create-pr with strict 403 gate, /api/scheduler/.../trigger)
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from hub.app import create_app
from hub.cdp_bridge import CDPBridge, CDPResponse, probe_ollama_instance
from hub.config_store import ConfigStore
from hub.engine_router import EngineRouter
from hub.models import (
    EscalateRequest,
    HubConfig,
    OllamaInstance,
    RepoScheduleConfig,
    RoleModelConfig,
    SeniorReviewResult,
    Suggestion,
    TaskStatus,
)
from hub.scanner import find_suggestions
from hub.scheduler import BackgroundScheduler


# --- Task 2 Tests: Ollama Probe, CDP Model Discovery & Escalation, Senior Review ---


@pytest.mark.asyncio
async def test_probe_ollama_instance_unreachable():
    """Unreachable Ollama endpoint returns structured offline result without raising."""
    result = await probe_ollama_instance("http://127.0.0.1:54321", timeout=0.5)
    assert result["online_status"] is False
    assert isinstance(result["latency_ms"], (int, float))
    assert result["models_list"] == []
    assert result["error"] is not None


@pytest.mark.asyncio
async def test_probe_ollama_instance_success():
    """Successful Ollama /api/tags response returns model list and online_status=True."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "models": [{"name": "qwen2.5-coder:latest"}, {"name": "deepseek-coder:6.7b"}]
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
        result = await probe_ollama_instance("http://localhost:11434", timeout=2.0)
        assert result["online_status"] is True
        assert "qwen2.5-coder:latest" in result["models_list"]
        assert "deepseek-coder:6.7b" in result["models_list"]
        assert result["error"] is None


@pytest.mark.asyncio
async def test_cdp_model_picker_and_escalate_offline():
    """CDPBridge returns fallback models and graceful failure when CDP port is closed."""
    bridge = CDPBridge(cdp_host="127.0.0.1", cdp_port=9999, timeout=0.5)
    models = await bridge.get_available_models()
    assert "Gemini 4 Argon (Low)" in models
    assert "Gemini 2.5 Flash" in models

    req = EscalateRequest(
        repo="jules",
        worktree_path="/tmp/wt1",
        branch="feat-test",
        diff_summary="+ test diff",
        test_status="passed",
    )
    resp = await bridge.select_model_and_escalate("Gemini 4 Argon (Low)", req)
    assert resp.success is False
    assert "CDP" in resp.message


@pytest.mark.asyncio
async def test_cdp_select_model_and_escalate_success():
    """Mocked CDP WebSocket communication returns success and response_data."""
    bridge = CDPBridge(cdp_host="127.0.0.1", cdp_port=9000, timeout=1.0)
    with patch.object(bridge, "get_debugger_url", new_callable=AsyncMock, return_value=("ws://127.0.0.1:9000/devtools/page/1", None)):
        mock_ws = AsyncMock()
        mock_ws.recv.return_value = '{"id": 3, "result": {"result": {"value": {"status": "escalated"}}}}'
        mock_ws.__aenter__.return_value = mock_ws

        with patch("websockets.connect", return_value=mock_ws):
            req = EscalateRequest(
                repo="jules",
                worktree_path="/tmp/wt1",
                branch="feat-test",
                diff_summary="+ test diff",
                test_status="passed",
            )
            resp = await bridge.select_model_and_escalate("Gemini 4 Argon (Low)", req)
            assert resp.success is True
            assert "Gemini 4 Argon (Low)" in resp.message


@pytest.mark.asyncio
async def test_run_senior_review_gate():
    """EngineRouter senior review gate enforces scope ceiling, safety, and test checks."""
    router = EngineRouter()
    senior_config = RoleModelConfig(provider="cdp", model_name="Gemini 4 Argon (Low)")

    # 1. Scope ceiling violation (>50 lines) must be REJECTED
    huge_diff = "\n".join([f"+ line {i}" for i in range(60)])
    res_huge = await router.run_senior_review(
        diff_text=huge_diff,
        test_status="passed",
        issue_context="Fix performance",
        senior_config=senior_config,
    )
    assert res_huge.verdict == "REJECTED"
    assert "scope ceiling" in res_huge.simple_explanation.lower()

    # 2. Valid atomic diff (<50 lines) with passed test gate -> APPROVED
    atomic_diff = "@@ -1,3 +1,3 @@\n- old_call()\n+ new_optimized_call()"
    res_valid = await router.run_senior_review(
        diff_text=atomic_diff,
        test_status="passed",
        issue_context="Optimize query",
        senior_config=senior_config,
    )
    assert res_valid.verdict == "APPROVED"
    assert res_valid.reviewer_model == "Gemini 4 Argon (Low)"

    # 3. Hazardous code patterns (eval, os.system) -> REJECTED
    hazardous_diff = "@@ -1,1 +1,2 @@\n+ import os\n+ eval(user_input)"
    res_hazard = await router.run_senior_review(
        diff_text=hazardous_diff,
        test_status="passed",
        issue_context="Dynamic runner",
        senior_config=senior_config,
    )
    assert res_hazard.verdict == "REJECTED"
    assert "hazard" in res_hazard.simple_explanation.lower() or "risk" in res_hazard.security_notes.lower()

    # 4. Failed tests -> REJECTED
    res_failed_tests = await router.run_senior_review(
        diff_text=atomic_diff,
        test_status="failed",
        issue_context="Feature",
        senior_config=senior_config,
    )
    assert res_failed_tests.verdict == "REJECTED"


# --- Task 3 Tests: Scanner Ignored IDs, Scheduler, and REST API ---


def test_scanner_ignored_ids_filtering(tmp_path: Path):
    """Scanner filters out suggestions whose IDs are present in ignored_ids."""
    sample_file = tmp_path / "sample.py"
    sample_file.write_text(
        "import subprocess\n"
        "subprocess.run('echo test', shell=True)\n",
        encoding="utf-8",
    )

    all_suggs = find_suggestions(tmp_path, mode="sentinel", category="all")
    assert len(all_suggs) >= 1
    target_id = all_suggs[0].id

    filtered_suggs = find_suggestions(
        tmp_path,
        mode="sentinel",
        category="all",
        ignored_ids={target_id},
    )
    assert not any(s.id == target_id for s in filtered_suggs)


@pytest.mark.asyncio
async def test_scheduler_trigger_repo(tmp_path: Path):
    """BackgroundScheduler triggers repo schedule, updates timestamps, and respects pending limits."""
    cfg_file = tmp_path / "cfg.json"
    st_file = tmp_path / "st.json"
    store = ConfigStore(cfg_file, st_file)
    cfg = HubConfig(
        repo_schedules=[
            RepoScheduleConfig(
                repo_name="jules",
                enabled=True,
                interval_hours=6,
                max_pending_worktrees=3,
            )
        ]
    )
    store.save_config(cfg)

    scheduler = BackgroundScheduler(config_store=store)
    res = await scheduler.trigger_repo("jules")
    assert res["repo_name"] == "jules"
    assert res["triggered"] is True
    assert res["status"] == "scheduled"

    updated_cfg = store.load_config()
    assert updated_cfg.repo_schedules[0].last_run_at is not None
    assert updated_cfg.repo_schedules[0].next_run_at is not None

    # Test scheduler start and stop lifecycle cleanly
    await scheduler.start()
    assert scheduler._running is True
    await scheduler.stop()
    assert scheduler._running is False


@pytest.mark.asyncio
async def test_scheduler_worktree_limit(tmp_path: Path):
    """BackgroundScheduler halts additional worktree spawning when max_pending_worktrees is reached."""
    cfg_file = tmp_path / "cfg.json"
    st_file = tmp_path / "st.json"
    store = ConfigStore(cfg_file, st_file)
    cfg = HubConfig(
        repo_schedules=[
            RepoScheduleConfig(
                repo_name="jules",
                enabled=True,
                interval_hours=6,
                max_pending_worktrees=2,
            )
        ]
    )
    store.save_config(cfg)

    mock_wm = MagicMock()
    mock_wt1 = MagicMock(repo_name="jules", is_active=True)
    mock_wt2 = MagicMock(repo_name="jules", is_active=True)
    mock_wm.list_worktrees.return_value = [mock_wt1, mock_wt2]

    scheduler = BackgroundScheduler(config_store=store, worktree_manager=mock_wm)
    res = await scheduler.trigger_repo("jules")
    assert res["triggered"] is True
    assert res["status"] == "capped_pending_worktrees"
    assert res["active_worktrees"] == 2


def test_api_config_routes(tmp_path: Path):
    """Test GET and PUT on /api/config."""
    store = ConfigStore(tmp_path / "cfg.json", tmp_path / "st.json")
    app = create_app(config_store=store)
    client = TestClient(app)

    get_resp = client.get("/api/config")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert len(data["ollama_instances"]) == 1
    assert "localhost" in data["ollama_instances"][0]["url"]
    assert data["cdp_port"] == 9000

    data["max_diff_lines"] = 35
    put_resp = client.put("/api/config", json=data)
    assert put_resp.status_code == 200
    assert put_resp.json()["max_diff_lines"] == 35
    assert store.load_config().max_diff_lines == 35


def test_api_ollama_and_cdp_routes(tmp_path: Path):
    """Test /api/ollama/test, /api/ollama/instances/{id}/models, and /api/cdp/models."""
    store = ConfigStore(tmp_path / "cfg.json", tmp_path / "st.json")
    app = create_app(config_store=store)
    client = TestClient(app)

    # 1. /api/ollama/test
    inst_payload = {
        "id": 1,
        "name": "GPU Server",
        "url": "http://127.0.0.1:54321",
        "enabled": True,
        "timeout_sec": 1,
    }
    test_resp = client.post("/api/ollama/test", json=inst_payload)
    assert test_resp.status_code == 200
    assert test_resp.json()["online_status"] is False

    # 2. /api/ollama/instances/1/models
    models_resp = client.get("/api/ollama/instances/1/models")
    assert models_resp.status_code == 200
    assert "online_status" in models_resp.json()

    # 3. /api/ollama/instances/999/models (Not found)
    nf_resp = client.get("/api/ollama/instances/999/models")
    assert nf_resp.status_code == 404

    # 4. /api/cdp/models
    cdp_resp = client.get("/api/cdp/models")
    assert cdp_resp.status_code == 200
    assert "Gemini 4 Argon (Low)" in cdp_resp.json()


def test_api_suggestions_discard(tmp_path: Path):
    """Test discarding suggestion marks it in state and filters from subsequent scans."""
    store = ConfigStore(tmp_path / "cfg.json", tmp_path / "st.json")
    app = create_app(config_store=store)
    client = TestClient(app)

    discard_resp = client.post("/api/suggestions/sugg_test_100/discard")
    assert discard_resp.status_code == 200
    assert discard_resp.json()["discarded_id"] == "sugg_test_100"

    state = store.load_state()
    assert "sugg_test_100" in state.ignored_suggestions


def test_api_tasks_senior_review_and_strict_create_pr_gate(tmp_path: Path):
    """Test /api/tasks/{task_id}/senior-review and /api/tasks/{task_id}/create-pr 403 Gate."""
    store = ConfigStore(tmp_path / "cfg.json", tmp_path / "st.json")
    app = create_app(config_store=store)
    client = TestClient(app)

    # 1. Run senior review via API with valid atomic diff
    rev_resp = client.post(
        "/api/tasks/task_gate_1/senior-review",
        json={"diff_text": "@@ -1,2 +1,2 @@\n- old\n+ new"},
    )
    assert rev_resp.status_code == 200
    rev_data = rev_resp.json()
    assert rev_data["verdict"] == "APPROVED"
    assert store.get_task_review("task_gate_1").verdict == "APPROVED"

    # 2. Approved task -> create-pr succeeds (200 OK)
    pr_resp_ok = client.post("/api/tasks/task_gate_1/create-pr")
    assert pr_resp_ok.status_code == 200
    assert pr_resp_ok.json()["success"] is True

    # 3. Unreviewed task -> 403 Forbidden
    pr_unreviewed = client.post("/api/tasks/task_unreviewed/create-pr")
    assert pr_unreviewed.status_code == 403
    assert "not been APPROVED" in pr_unreviewed.json()["detail"]

    # 4. Rejected task -> 403 Forbidden
    store.set_task_review(
        "task_rejected",
        SeniorReviewResult(
            verdict="REJECTED",
            simple_explanation="Scope limit exceeded",
            security_notes="Security check failed",
            reviewer_model="Gemini 4 Argon (Low)",
        ),
    )
    pr_rejected = client.post("/api/tasks/task_rejected/create-pr")
    assert pr_rejected.status_code == 403
    assert "REJECTED" in pr_rejected.json()["detail"]


def test_api_scheduler_trigger(tmp_path: Path):
    """Test POST /api/scheduler/{repo_name}/trigger."""
    store = ConfigStore(tmp_path / "cfg.json", tmp_path / "st.json")
    app = create_app(config_store=store)
    client = TestClient(app)

    resp = client.post("/api/scheduler/jules/trigger")
    assert resp.status_code == 200
    assert resp.json()["repo_name"] == "jules"
    assert resp.json()["triggered"] is True
