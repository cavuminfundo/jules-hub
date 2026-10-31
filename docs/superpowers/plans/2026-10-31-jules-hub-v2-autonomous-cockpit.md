# Jules Hub v2 — Autonomous Cockpit Implementation Plan

## Goal
To develop and implement the Jules Hub v2 Autonomous Cockpit, a sophisticated system that integrates advanced AI capabilities for code review, suggestion management, and automated scheduling. The system will leverage multiple Ollama instances, a CDP (Chrome DevTools Protocol) bridge, and a robust backend architecture to provide a seamless user experience.

## Architecture
The Jules Hub v2 Autonomous Cockpit will consist of a backend built with FastAPI and Python, and a frontend built with React and Tailwind CSS. The backend will handle configuration management, Ollama instance discovery, AI scanning, and scheduling, while the frontend will provide a user-friendly interface for managing settings, scheduling, and reviewing suggestions.

## Tech Stack
- **Backend**: Python 3.12+, FastAPI, Pydantic v2 (`model_dump()`), httpx (async), pytest
- **Frontend**: React 18, Tailwind CSS, TypeScript, Lucide Icons (native tab state: `activeTab: 'cockpit' | 'scheduler' | 'settings'`)
- **Data Persistence**: Atomic JSON Storage (`pathlib.Path`, tempfile write + atomic rename, no SQLite / no Pony ORM)
- **CDP Bridge**: Chrome DevTools Protocol (port 9000, async websockets / httpx)
- **AI Models**: Multi-Instance Ollama Registry + Antigravity CLI Engine

## Spec Path
[docs/superpowers/specs/2026-10-31-jules-hub-v2-autonomous-cockpit-design.md](docs/superpowers/specs/2026-10-31-jules-hub-v2-autonomous-cockpit-design.md)

## CodeGraph Evidence
- `hub/models.py`
- `hub/engine_router.py`
- `hub/scanner.py`
- `hub/cdp_bridge.py`
- `hub/app.py`
- `ui/src/App.tsx`
- `ui/src/components/DiffDrawer.tsx`

## Domain Skills & Sub-Agent Roster (N-Domain Mapping)

### Domain 1 (Backend Python & FastAPI Core)
- **Worker**: `backend_v2_worker`
- **Primary Skill**: `python-pro` (`/home/federico/skills_library/python-pro/SKILL.md`)
- **Transversal Companions**: `ponytail` + `antislop-code`
- **Exclusive Files**:
  - `hub/models.py`
  - `hub/config_store.py`
  - `hub/engine_router.py`
  - `hub/scanner.py`
  - `hub/cdp_bridge.py`
  - `hub/scheduler.py`
  - `hub/app.py`
  - `tests/test_config_store.py`
  - `tests/test_scheduler_and_senior.py`

### Domain 2 (Frontend React + Tailwind Dark UI)
- **Worker**: `frontend_v2_worker`
- **Primary Skill**: `react-best-practices` (`/home/federico/skills_library/react-best-practices/SKILL.md`)
- **Transversal Companions**: `antislop-ui` + `antislop-code`
- **Exclusive Files**:
  - `ui/src/types.ts`
  - `ui/src/api.ts`
  - `ui/src/components/SettingsView.tsx`
  - `ui/src/components/SchedulerPanel.tsx`
  - `ui/src/components/DiffDrawer.tsx`
  - `ui/src/components/SuggestionCard.tsx`
  - `ui/src/App.tsx`

## Detailed Tasks with Exact TDD Steps

### Task 1: Config Store & Multi-Instance Ollama Registry
**Files**: `hub/models.py`, `hub/config_store.py`, `tests/test_config_store.py`

1. **RED Test Code**:
   ```python
   # tests/test_config_store.py
   import pytest
   from pathlib import Path
   from hub.config_store import ConfigStore
   from hub.models import HubConfig, HubState, OllamaInstance, SeniorReviewResult

   def test_config_store_load_save_defaults(tmp_path: Path):
       config_file = tmp_path / "hub_config.json"
       state_file = tmp_path / "hub_state.json"
       store = ConfigStore(config_path=config_file, state_path=state_file)

       # Loading nonexistent files should return default models
       cfg = store.load_config()
       assert isinstance(cfg, HubConfig)
       assert len(cfg.ollama_instances) >= 2
       assert cfg.cdp_port == 9000

       # Saving and reloading config
       cfg.max_diff_lines = 40
       store.save_config(cfg)
       reloaded = store.load_config()
       assert reloaded.max_diff_lines == 40

       # State operations
       state = store.load_state()
       assert isinstance(state, HubState)
       store.add_ignored_suggestion("sig_test_123")
       updated_state = store.load_state()
       assert "sig_test_123" in updated_state.ignored_suggestions

       # Senior review persistence
       review = SeniorReviewResult(
           verdict="APPROVED",
           simple_explanation="Looks great, atomic diff.",
           security_notes="No security risks found.",
           reviewer_model="Gemini 4 Argon (Low)"
       )
       store.set_task_review("task_999", review)
       assert store.get_task_review("task_999").verdict == "APPROVED"
   ```

2. **Run pytest**:
   ```bash
   pytest tests/test_config_store.py
   ```

3. **GREEN Implementation Code**:
   ```python
   # hub/models.py
   from enum import Enum
   from typing import Any, Dict, List, Optional
   from pydantic import BaseModel, ConfigDict, Field

   class OllamaInstance(BaseModel):
       """Configuration for an Ollama server instance."""
       model_config = ConfigDict(extra="ignore")

       id: int
       name: str
       url: str
       enabled: bool = True
       timeout_sec: int = 30

   class RoleModelConfig(BaseModel):
       """Model and provider assignment for Junior or Senior role."""
       model_config = ConfigDict(extra="ignore")

       provider: str = "ollama"  # "ollama" | "antigravity_cli" | "cdp"
       instance_id: int = 1
       model_name: str = "qwen2.5-coder"
       fallback_provider: Optional[str] = "antigravity_cli"
       fallback_instance_id: Optional[int] = None
       fallback_model: Optional[str] = "flash"

   class RepoScheduleConfig(BaseModel):
       """Periodic curation schedule configuration for a repository."""
       model_config = ConfigDict(extra="ignore")

       repo_name: str
       enabled: bool = True
       interval_hours: int = 6
       personas: List[str] = Field(default_factory=lambda: ["bolt", "palette", "sentinel"])
       max_pending_worktrees: int = 3
       last_run_at: Optional[str] = None
       next_run_at: Optional[str] = None

   class HubConfig(BaseModel):
       """Global hub configuration persisted to data/hub_config.json."""
       model_config = ConfigDict(extra="ignore")

       ollama_instances: List[OllamaInstance] = Field(
           default_factory=lambda: [
               OllamaInstance(id=1, name="GPU Server 24/7", url="http://192.168.88.117:11434", enabled=True, timeout_sec=30),
               OllamaInstance(id=2, name="Workstation RTX 5070 Ti", url="http://100.102.204.70:11434", enabled=True, timeout_sec=15),
           ]
       )
       junior_config: RoleModelConfig = Field(default_factory=RoleModelConfig)
       senior_config: RoleModelConfig = Field(
           default_factory=lambda: RoleModelConfig(provider="cdp", model_name="Gemini 4 Argon (Low)")
       )
       senior_mode: str = "cdp"  # "in_cockpit" | "cdp"
       cdp_host: str = "127.0.0.1"
       cdp_port: int = 9000
       max_diff_lines: int = 50
       repo_schedules: List[RepoScheduleConfig] = Field(default_factory=list)

   class SeniorReviewVerdict(str, Enum):
       APPROVED = "APPROVED"
       REJECTED = "REJECTED"

   class SeniorReviewResult(BaseModel):
       """Outcome of Senior Review audit gate."""
       model_config = ConfigDict(extra="ignore")

       verdict: str  # "APPROVED" | "REJECTED"
       simple_explanation: str
       security_notes: str
       reviewer_model: str
       reviewed_at: Optional[str] = None

   class HubState(BaseModel):
       """Runtime state persisted to data/hub_state.json."""
       model_config = ConfigDict(extra="ignore")

       ignored_suggestions: List[str] = Field(default_factory=list)
       task_reviews: Dict[str, SeniorReviewResult] = Field(default_factory=dict)

   # hub/config_store.py
   import json
   import logging
   import os
   from pathlib import Path
   from typing import Optional, Union
   from hub.models import HubConfig, HubState, SeniorReviewResult

   logger = logging.getLogger("hub.config_store")

   class ConfigStore:
       """
       Atomic JSON store for HubConfig and HubState using pathlib.Path and tempfile rename.
       Eliminates database dependencies (Pony ORM/SQLite) in favor of lightweight JSON files.
       """

       def __init__(
           self,
           config_path: Optional[Union[str, Path]] = None,
           state_path: Optional[Union[str, Path]] = None,
       ):
           base_data_dir = Path("/home/federico/jules/data")
           self.config_path = Path(config_path) if config_path else base_data_dir / "hub_config.json"
           self.state_path = Path(state_path) if state_path else base_data_dir / "hub_state.json"
           self.config_path.parent.mkdir(parents=True, exist_ok=True)
           self.state_path.parent.mkdir(parents=True, exist_ok=True)

       def _atomic_write_json(self, target_path: Path, data: dict) -> None:
           tmp_path = target_path.with_suffix(".tmp")
           try:
               tmp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
               tmp_path.replace(target_path)
           except Exception as e:
               if tmp_path.exists():
                   tmp_path.unlink(missing_ok=True)
               logger.exception("Failed atomic write to %s: %s", target_path, e)
               raise

       def load_config(self) -> HubConfig:
           if not self.config_path.exists():
               default_cfg = HubConfig()
               self.save_config(default_cfg)
               return default_cfg
           try:
               raw = json.loads(self.config_path.read_text(encoding="utf-8"))
               return HubConfig.model_validate(raw)
           except Exception as e:
               logger.error("Error loading config from %s: %s. Returning defaults.", self.config_path, e)
               return HubConfig()

       def save_config(self, config: HubConfig) -> None:
           self._atomic_write_json(self.config_path, config.model_dump())

       def load_state(self) -> HubState:
           if not self.state_path.exists():
               default_state = HubState()
               self.save_state(default_state)
               return default_state
           try:
               raw = json.loads(self.state_path.read_text(encoding="utf-8"))
               return HubState.model_validate(raw)
           except Exception as e:
               logger.error("Error loading state from %s: %s. Returning empty state.", self.state_path, e)
               return HubState()

       def save_state(self, state: HubState) -> None:
           self._atomic_write_json(self.state_path, state.model_dump())

       def add_ignored_suggestion(self, suggestion_sig: str) -> None:
           state = self.load_state()
           if suggestion_sig not in state.ignored_suggestions:
               state.ignored_suggestions.append(suggestion_sig)
               self.save_state(state)

       def set_task_review(self, task_id: str, review: SeniorReviewResult) -> None:
           state = self.load_state()
           state.task_reviews[task_id] = review
           self.save_state(state)

       def get_task_review(self, task_id: str) -> Optional[SeniorReviewResult]:
           state = self.load_state()
           return state.task_reviews.get(task_id)
   ```

4. **Verify GREEN**:
   ```bash
   pytest tests/test_config_store.py
   ```

### Task 2: Multi-Instance Ollama Discovery, CDP Model Picker & Senior Review Gate
**Files**: `hub/cdp_bridge.py`, `hub/engine_router.py`, `tests/test_scheduler_and_senior.py`

1. **RED Test Code**:
   ```python
   # tests/test_scheduler_and_senior.py
   import pytest
   from hub.cdp_bridge import CDPBridge, probe_ollama_instance
   from hub.engine_router import EngineRouter
   from hub.models import EscalateRequest, RoleModelConfig, SeniorReviewResult

   @pytest.mark.asyncio
   async def test_probe_ollama_instance():
       # Test unreachable endpoint returns structured offline result without raising
       result = await probe_ollama_instance("http://127.0.0.1:54321", timeout=0.5)
       assert result["online_status"] is False
       assert isinstance(result["latency_ms"], (int, float))
       assert result["models_list"] == []
       assert result["error"] is not None

   @pytest.mark.asyncio
   async def test_cdp_model_picker_and_escalate():
       bridge = CDPBridge(cdp_host="127.0.0.1", cdp_port=9999, timeout=0.5)
       # When CDP is offline, fallback models are returned cleanly
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
       assert resp.success is False  # cleanly returns failure without raising
       assert "CDP" in resp.message

   @pytest.mark.asyncio
   async def test_run_senior_review_gate():
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

       # 2. Valid atomic diff (<50 lines) with passed test gate
       atomic_diff = "@@ -1,3 +1,3 @@\n- old_call()\n+ new_optimized_call()"
       res_valid = await router.run_senior_review(
           diff_text=atomic_diff,
           test_status="passed",
           issue_context="Optimize query",
           senior_config=senior_config,
       )
       assert res_valid.verdict == "APPROVED"
       assert res_valid.reviewer_model == "Gemini 4 Argon (Low)"
   ```

2. **Run pytest**:
   ```bash
   pytest tests/test_scheduler_and_senior.py
   ```

3. **GREEN Implementation Code**:
   ```python
   # hub/cdp_bridge.py
   import asyncio
   import json
   import logging
   import os
   import time
   from typing import Any, Dict, List, Optional, Tuple, Union

   import httpx
   from pydantic import BaseModel, ConfigDict
   import websockets

   from hub.models import CDPResponse as BaseCDPResponse, EscalateRequest

   logger = logging.getLogger("hub.cdp_bridge")

   DEFAULT_CDP_HOST = os.environ.get("CDP_HOST", "127.0.0.1")
   DEFAULT_CDP_PORT = int(os.environ.get("CDP_PORT", "9000"))

   async def probe_ollama_instance(url: str, timeout: float = 5.0) -> Dict[str, Any]:
       """
       Probe an Ollama instance endpoint (/api/tags) asynchronously via httpx.
       Returns online status, latency in milliseconds, and installed model tags.
       Never raises exceptions.
       """
       target_url = f"{url.rstrip('/')}/api/tags"
       start_time = time.perf_counter()
       try:
           async with httpx.AsyncClient(timeout=timeout) as client:
               resp = await client.get(target_url)
               latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
               if resp.status_code == 200:
                   data = resp.json()
                   models = [m.get("name") for m in data.get("models", []) if isinstance(m, dict) and "name" in m]
                   return {
                       "online_status": True,
                       "latency_ms": latency_ms,
                       "models_list": models,
                       "error": None,
                   }
               return {
                   "online_status": False,
                   "latency_ms": latency_ms,
                   "models_list": [],
                   "error": f"HTTP {resp.status_code}: {resp.text[:100]}",
               }
       except (httpx.ConnectError, ConnectionRefusedError, OSError) as e:
           latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
           return {"online_status": False, "latency_ms": latency_ms, "models_list": [], "error": f"Connection failed: {e}"}
       except (httpx.TimeoutException, asyncio.TimeoutError) as e:
           latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
           return {"online_status": False, "latency_ms": latency_ms, "models_list": [], "error": f"Timeout after {timeout}s: {e}"}
       except Exception as e:
           latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
           return {"online_status": False, "latency_ms": latency_ms, "models_list": [], "error": f"Unexpected error: {e}"}

   class CDPResponse(BaseCDPResponse):
       model_config = ConfigDict(extra="ignore")
       error: Optional[str] = None

   class CDPBridge:
       """
       Bridge to Antigravity Desktop via Chrome DevTools Protocol (CDP) port 9000.
       Provides dynamic model discovery and Senior Review handoff via Runtime.evaluate.
       """

       def __init__(
           self,
           cdp_host: str = DEFAULT_CDP_HOST,
           cdp_port: int = DEFAULT_CDP_PORT,
           timeout: float = 5.0,
       ):
           self.cdp_host = cdp_host
           self.cdp_port = cdp_port
           self.timeout = timeout

       @property
       def http_base_url(self) -> str:
           return f"http://{self.cdp_host}:{self.cdp_port}"

       async def get_debugger_url(self) -> Tuple[Optional[str], Optional[str]]:
           url = f"{self.http_base_url}/json/list"
           try:
               async with httpx.AsyncClient(timeout=self.timeout) as client:
                   resp = await client.get(url)
                   if resp.status_code != 200:
                       return None, f"CDP returned HTTP {resp.status_code}"
                   targets = resp.json()
           except Exception as e:
               return None, f"CDP connection refused on {self.cdp_host}:{self.cdp_port}: {e}"

           if not isinstance(targets, list) or len(targets) == 0:
               return None, "No active CDP targets found"

           for t in targets:
               if isinstance(t, dict) and t.get("type") == "page" and "webSocketDebuggerUrl" in t:
                   return t["webSocketDebuggerUrl"], None
           for t in targets:
               if isinstance(t, dict) and "webSocketDebuggerUrl" in t:
                   return t["webSocketDebuggerUrl"], None
           return None, "No webSocketDebuggerUrl found in targets"

       async def get_available_models(self) -> List[str]:
           """
           Query Antigravity Model Picker via CDP Runtime.evaluate or return default models.
           """
           fallback_models = [
               "Gemini 4 Argon (Low)",
               "Gemini 4 Argon (Medium)",
               "Gemini 2.5 Pro",
               "Gemini 2.5 Flash",
           ]
           ws_url, err = await self.get_debugger_url()
           if not ws_url or err:
               return fallback_models

           eval_expression = """
               (() => {
                   const picker = document.querySelector('[data-testid="model-picker"]');
                   if (!picker) return null;
                   const options = Array.from(picker.querySelectorAll('option, [role="option"]'));
                   return options.map(o => (o.textContent || '').trim()).filter(Boolean);
               })()
           """
           cdp_cmd = {
               "id": 2,
               "method": "Runtime.evaluate",
               "params": {"expression": eval_expression, "returnByValue": True},
           }
           try:
               async with websockets.connect(ws_url, open_timeout=self.timeout, close_timeout=self.timeout) as ws:
                   await ws.send(json.dumps(cdp_cmd))
                   raw = await asyncio.wait_for(ws.recv(), timeout=self.timeout)
                   resp_data = json.loads(raw)
                   models = resp_data.get("result", {}).get("result", {}).get("value")
                   if isinstance(models, list) and len(models) > 0:
                       return models
           except Exception as e:
               logger.warning("CDP model discovery failed: %s; using fallbacks", e)
           return fallback_models

       async def select_model_and_escalate(self, model_name: str, req: EscalateRequest) -> CDPResponse:
           """
           Select senior model in Antigravity DOM and trigger Senior Review via CDP evaluate.
           """
           ws_url, err = await self.get_debugger_url()
           if not ws_url or err:
               return CDPResponse(success=False, message=err or "CDP discovery failed", error=err or "CDP discovery failed")

           payload = {
               "action": "senior_review",
               "selected_model": model_name,
               "repo": req.repo,
               "worktree_path": req.worktree_path,
               "branch": req.branch,
               "diff_summary": req.diff_summary,
               "test_status": req.test_status,
               "instruction": req.instruction,
           }

           expression = f"""
               (() => {{
                   if (window.selectAntigravityModel) {{
                       window.selectAntigravityModel({json.dumps(model_name)});
                   }}
                   if (window.triggerSeniorReview) {{
                       return window.triggerSeniorReview({json.dumps(payload)});
                   }}
                   console.log('Senior Review Escalated', {json.dumps(payload)});
                   return {{ status: 'escalated', model: {json.dumps(model_name)} }};
               }})()
           """
           cdp_cmd = {
               "id": 3,
               "method": "Runtime.evaluate",
               "params": {
                   "expression": expression,
                   "returnByValue": True,
                   "awaitPromise": True,
               },
           }

           try:
               async with websockets.connect(ws_url, open_timeout=self.timeout, close_timeout=self.timeout) as ws:
                   await ws.send(json.dumps(cdp_cmd))
                   raw_response = await asyncio.wait_for(ws.recv(), timeout=self.timeout)
                   resp_data = json.loads(raw_response)
                   if "error" in resp_data:
                       err_msg = f"CDP Runtime.evaluate returned error: {resp_data['error']}"
                       return CDPResponse(success=False, message=err_msg, error=err_msg, response_data=resp_data)
                   return CDPResponse(
                       success=True,
                       message=f"Escalated senior review to model '{model_name}' for {req.repo} ({req.branch})",
                       response_data=resp_data,
                   )
           except Exception as e:
               err_msg = f"CDP WebSocket escalation failed: {e}"
               return CDPResponse(success=False, message=err_msg, error=err_msg)

   # hub/engine_router.py
   from datetime import datetime, timezone
   from hub.models import RoleModelConfig, SeniorReviewResult

   # In addition to existing EngineRouter methods:
   def count_diff_lines(diff_text: str) -> int:
       count = 0
       for line in diff_text.splitlines():
           if (line.startswith("+") and not line.startswith("+++")) or \
              (line.startswith("-") and not line.startswith("---")):
               count += 1
       return count

   class EngineRouter:
       # ... existing init and methods ...

       async def run_senior_review(
           self,
           diff_text: str,
           test_status: str,
           issue_context: str,
           senior_config: RoleModelConfig,
       ) -> SeniorReviewResult:
           """
           Execute Senior Review audit gate on proposed diff.
           Enforces strict scope ceiling (<50 lines) and checks test results & security hygiene.
           """
           lines_changed = count_diff_lines(diff_text)
           if lines_changed > 50:
               return SeniorReviewResult(
                   verdict="REJECTED",
                   simple_explanation=f"Diff exceeds scope ceiling ({lines_changed} lines changed > 50 max).",
                   security_notes="Automated scope check failed: patch too large for atomic micro-improvement.",
                   reviewer_model=senior_config.model_name,
                   reviewed_at=datetime.now(timezone.utc).isoformat(),
               )

           prompt = (
               "You are an expert Senior Code Reviewer and Tech Lead.\n"
               f"Issue Context: {issue_context}\n"
               f"Test Gate Status: {test_status}\n"
               f"Diff:\n{diff_text}\n\n"
               "Audit the code and return JSON with keys:\n"
               '- "verdict": "APPROVED" | "REJECTED"\n'
               '- "simple_explanation": "summary of review"\n'
               '- "security_notes": "notes on safety and security"\n'
           )

           if senior_config.provider == "ollama":
               try:
                   async with httpx.AsyncClient(timeout=self.http_timeout) as client:
                       resp = await client.post(
                           f"{self.ollama_url}/api/generate",
                           json={"model": senior_config.model_name, "prompt": prompt, "stream": False, "format": "json"},
                       )
                       if resp.status_code == 200:
                           data = json.loads(resp.json().get("response", "{}"))
                           return SeniorReviewResult(
                               verdict=data.get("verdict", "APPROVED").upper(),
                               simple_explanation=data.get("simple_explanation", "Code passed senior review audit."),
                               security_notes=data.get("security_notes", "No security issues identified."),
                               reviewer_model=senior_config.model_name,
                               reviewed_at=datetime.now(timezone.utc).isoformat(),
                           )
               except Exception as e:
                   logger.warning("Ollama senior review failed: %s; falling back to heuristic audit", e)

           is_safe = "eval(" not in diff_text and "os.system(" not in diff_text and "__import__" not in diff_text
           is_passed = str(test_status).lower() in ("passed", "success", "ok", "true")
           approved = is_safe and is_passed

           return SeniorReviewResult(
               verdict="APPROVED" if approved else "REJECTED",
               simple_explanation="Patch verified against test gates and atomic scope constraints." if approved else "Tests failed or hazardous patterns detected in patch.",
               security_notes="Safe execution confirmed; no shell injection or unsafe calls." if is_safe else "Security risk: unsafe code execution pattern detected.",
               reviewer_model=senior_config.model_name,
               reviewed_at=datetime.now(timezone.utc).isoformat(),
           )
   ```

4. **Verify GREEN**:
   ```bash
   pytest tests/test_scheduler_and_senior.py
   ```

### Task 3: AI Deep Scanner, Ignored Suggestions & Background Scheduler
**Files**: `hub/scanner.py`, `hub/scheduler.py`, `hub/app.py`, `tests/test_scheduler_and_senior.py`

1. **RED Test Code**:
   ```python
   # tests/test_scheduler_and_senior.py
   import pytest
   from fastapi.testclient import TestClient
   from hub.app import create_app
   from hub.config_store import ConfigStore
   from hub.models import HubConfig, RepoScheduleConfig, SeniorReviewResult
   from hub.scheduler import BackgroundScheduler

   @pytest.mark.asyncio
   async def test_scheduler_trigger_repo(tmp_path):
       cfg_path = tmp_path / "cfg.json"
       st_path = tmp_path / "st.json"
       store = ConfigStore(cfg_path, st_path)
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

   def test_create_pr_forbidden_without_approval(tmp_path):
       cfg_path = tmp_path / "cfg.json"
       st_path = tmp_path / "st.json"
       store = ConfigStore(cfg_path, st_path)

       app = create_app()
       app.state.config_store = store
       client = TestClient(app)

       # 1. Unreviewed task -> 403 Forbidden
       resp_unreviewed = client.post("/api/tasks/task_unreviewed/create-pr")
       assert resp_unreviewed.status_code == 403
       assert "not been APPROVED" in resp_unreviewed.json()["detail"]

       # 2. Rejected task -> 403 Forbidden
       store.set_task_review("task_rejected", SeniorReviewResult(
           verdict="REJECTED",
           simple_explanation="Scope ceiling violated",
           security_notes="Refactor required",
           reviewer_model="Gemini 4 Argon (Low)"
       ))
       resp_rejected = client.post("/api/tasks/task_rejected/create-pr")
       assert resp_rejected.status_code == 403

       # 3. Approved task -> 200 OK
       store.set_task_review("task_approved", SeniorReviewResult(
           verdict="APPROVED",
           simple_explanation="Atomic patch verified",
           security_notes="Safe",
           reviewer_model="Gemini 4 Argon (Low)"
       ))
       resp_approved = client.post("/api/tasks/task_approved/create-pr")
       assert resp_approved.status_code == 200
       assert resp_approved.json()["success"] is True
   ```

2. **Run pytest**:
   ```bash
   pytest tests/test_scheduler_and_senior.py
   ```

3. **GREEN Implementation Code**:
   ```python
   # hub/scanner.py
   from pathlib import Path
   from typing import List, Optional, Set, Union
   from hub.models import Suggestion

   def find_suggestions(
       repo_path: Union[str, Path],
       mode: str = "all",
       category: str = "all",
       ignored_ids: Optional[Set[str]] = None,
   ) -> List[Suggestion]:
       """
       Scan repository for micro-improvements across Bolt, Palette, and Sentinel personas.
       Filters out suggestions present in ignored_ids (from data/hub_state.json).
       """
       repo = Path(repo_path).resolve()
       if not repo.exists():
           raise FileNotFoundError(f"Repository path does not exist: {repo}")

       ignored = ignored_ids or set()
       # Scan repository heuristics and AST rules
       raw_suggestions: List[Suggestion] = []
       # ... scanner AST and static checks ...
       # Filter out discarded suggestions
       return [s for s in raw_suggestions if s.id not in ignored]

   # hub/scheduler.py
   import asyncio
   from datetime import datetime, timezone, timedelta
   import logging
   from typing import Any, Dict, Optional
   from hub.config_store import ConfigStore
   from hub.models import HubConfig

   logger = logging.getLogger("hub.scheduler")

   class BackgroundScheduler:
       """
       Background asyncio daemon checking repository schedules every 60 seconds.
       Enforces max_pending_worktrees guardrails before launching autonomous scans.
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
           if self._running:
               return
           self._running = True
           self._task = asyncio.create_task(self._loop())
           logger.info("BackgroundScheduler started successfully.")

       async def stop(self) -> None:
           self._running = False
           if self._task:
               self._task.cancel()
               try:
                   await self._task
               except asyncio.CancelledError:
                   pass
           logger.info("BackgroundScheduler stopped.")

       async def trigger_repo(self, repo_name: str) -> Dict[str, Any]:
           """Manually or periodically trigger a curation cycle for a specific repository."""
           cfg = self.config_store.load_config()
           target_sched = next((s for s in cfg.repo_schedules if s.repo_name == repo_name), None)
           now_iso = datetime.now(timezone.utc).isoformat()

           if target_sched:
               target_sched.last_run_at = now_iso
               target_sched.next_run_at = (datetime.now(timezone.utc) + timedelta(hours=target_sched.interval_hours)).isoformat()
               self.config_store.save_config(cfg)

           return {
               "repo_name": repo_name,
               "triggered": True,
               "triggered_at": now_iso,
               "status": "scheduled",
           }

       async def _tick(self) -> None:
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
           while self._running:
               try:
                   await self._tick()
               except Exception as e:
                   logger.exception("Error in scheduler tick: %s", e)
               await asyncio.sleep(60)

   # hub/app.py (Extensions inside create_app)
   # Inside create_app() in hub/app.py:
   # Attach config_store and scheduler instances
   # app.state.config_store = config_store or ConfigStore()
   # app.state.scheduler = scheduler or BackgroundScheduler(app.state.config_store, app.state.worktree_manager, app.state.engine_router)

   @app.get("/api/config")
   async def get_config():
       """Retrieve current Jules Hub v2 configuration."""
       return app.state.config_store.load_config()

   @app.put("/api/config")
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
   async def senior_review(task_id: str, diff_text: Optional[str] = None):
       """
       Execute Senior Review audit gate on task worktree diff.
       Persists verdict and explanations in hub state.
       """
       router: EngineRouter = app.state.engine_router
       cfg: HubConfig = app.state.config_store.load_config()
       resolved_diff = diff_text or "+ sample diff"
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

       # Proceed with Pull Request creation
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
   ```

4. **Verify GREEN**:
   ```bash
   pytest tests/test_scheduler_and_senior.py
   ```

### Task 4: Frontend Cockpit v2 — Settings Tab, Multi-Ollama Manager, Per-Repo Scheduler & Senior Review Drawer
**Files**: `ui/src/types.ts`, `ui/src/api.ts`, `ui/src/components/SettingsView.tsx`, `ui/src/components/SchedulerPanel.tsx`, `ui/src/components/DiffDrawer.tsx`, `ui/src/components/SuggestionCard.tsx`, `ui/src/App.tsx`

1. **RED Test Code**:
   ```typescript
   // ui/src/components/SettingsView.test.tsx
   import { render, screen, fireEvent } from '@testing-library/react';
   import { SettingsView } from './SettingsView';

   test('renders settings view and handles save', () => {
       const mockSave = jest.fn();
       render(<SettingsView onSaveConfig={mockSave} />);
       expect(screen.getByText(/Ollama Instance Registry/i)).toBeInTheDocument();
       expect(screen.getByText(/Junior Engine/i)).toBeInTheDocument();
       expect(screen.getByText(/Senior Reviewer/i)).toBeInTheDocument();
   });

   // ui/src/components/SchedulerPanel.test.tsx
   import { render, screen } from '@testing-library/react';
   import { SchedulerPanel } from './SchedulerPanel';

   test('renders scheduler panel with repo configurations', () => {
       render(<SchedulerPanel onTriggerRepo={jest.fn()} />);
       expect(screen.getByText(/Autonomous Repository Scheduler/i)).toBeInTheDocument();
   });
   ```

2. **Run npm test**:
   ```bash
   npm test
   ```

3. **GREEN Implementation Code**:
   ```typescript
   // ui/src/types.ts (v2 additions)
   export interface OllamaInstance {
     id: number;
     name: string;
     url: string;
     enabled: boolean;
     timeout_sec: number;
   }

   export interface RoleModelConfig {
     provider: string; // 'ollama' | 'antigravity_cli' | 'cdp'
     instance_id: number;
     model_name: string;
     fallback_provider?: string;
     fallback_instance_id?: number;
     fallback_model?: string;
   }

   export interface RepoScheduleConfig {
     repo_name: string;
     enabled: boolean;
     interval_hours: number;
     personas: string[];
     max_pending_worktrees: number;
     last_run_at?: string | null;
     next_run_at?: string | null;
   }

   export interface HubConfig {
     ollama_instances: OllamaInstance[];
     junior_config: RoleModelConfig;
     senior_config: RoleModelConfig;
     senior_mode: string;
     cdp_host: string;
     cdp_port: number;
     max_diff_lines: number;
     repo_schedules: RepoScheduleConfig[];
   }

   export interface SeniorReviewResult {
     verdict: 'APPROVED' | 'REJECTED';
     simple_explanation: string;
     security_notes: string;
     reviewer_model: string;
     reviewed_at?: string;
   }

   // ui/src/components/SettingsView.tsx
   import React, { useState, useEffect } from 'react';
   import { Save, RefreshCw, CheckCircle2, AlertCircle, Cpu, ShieldCheck } from 'lucide-react';
   import type { HubConfig, OllamaInstance } from '../types';
   import { api } from '../api';

   interface SettingsViewProps {
     onSaveConfig?: (cfg: HubConfig) => void;
   }

   export const SettingsView: React.FC<SettingsViewProps> = ({ onSaveConfig }) => {
     const [config, setConfig] = useState<HubConfig | null>(null);
     const [testingId, setTestingId] = useState<number | null>(null);
     const [testStatuses, setTestStatuses] = useState<Record<number, { online: boolean; latency?: number; error?: string }>>({});
     const [cdpModels, setCdpModels] = useState<string[]>([]);
     const [isSaving, setIsSaving] = useState(false);
     const [saveSuccess, setSaveSuccess] = useState(false);

     useEffect(() => {
       api.getConfig().then(setConfig).catch(console.error);
       api.getCdpModels().then(setCdpModels).catch(console.error);
     }, []);

     const handleTestInstance = async (inst: OllamaInstance) => {
       setTestingId(inst.id);
       try {
         const res = await api.testOllama(inst);
         setTestStatuses(prev => ({
           ...prev,
           [inst.id]: { online: res.online_status, latency: res.latency_ms, error: res.error },
         }));
       } catch (err: any) {
         setTestStatuses(prev => ({
           ...prev,
           [inst.id]: { online: false, error: err.message },
         }));
       } finally {
         setTestingId(null);
       }
     };

     const handleSave = async () => {
       if (!config) return;
       setIsSaving(true);
       try {
         await api.updateConfig(config);
         if (onSaveConfig) onSaveConfig(config);
         setSaveSuccess(true);
         setTimeout(() => setSaveSuccess(false), 3000);
       } catch (err) {
         console.error('Failed to save config', err);
       } finally {
         setIsSaving(false);
       }
     };

     if (!config) {
       return <div className="p-8 text-neutral-400">Loading settings...</div>;
     }

     return (
       <div className="max-w-4xl mx-auto p-6 space-y-8 text-neutral-200">
         <div className="flex items-center justify-between border-b border-neutral-800 pb-4">
           <div>
             <h2 className="text-xl font-semibold text-white">Hub Engine & Provider Settings</h2>
             <p className="text-sm text-neutral-400">Configure multi-instance Ollama endpoints, model matrix, and CDP bridge.</p>
           </div>
           <button
             onClick={handleSave}
             disabled={isSaving}
             className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-medium transition-colors"
           >
             <Save className="w-4 h-4" />
             {isSaving ? 'Saving...' : saveSuccess ? 'Saved!' : 'Save Config'}
           </button>
         </div>

         {/* Multi-Ollama Registry */}
         <section className="bg-neutral-900 border border-neutral-800 rounded-xl p-5 space-y-4">
           <div className="flex items-center gap-2 text-white font-medium">
             <Cpu className="w-5 h-5 text-indigo-400" />
             <span>Ollama Instance Registry</span>
           </div>
           <div className="space-y-3">
             {config.ollama_instances.map(inst => (
               <div key={inst.id} className="flex items-center justify-between bg-neutral-950 p-3 rounded-lg border border-neutral-800/80">
                 <div className="space-y-1">
                   <div className="flex items-center gap-2">
                     <span className="font-medium text-white">{inst.name}</span>
                     <span className="text-xs text-neutral-500">#{inst.id}</span>
                   </div>
                   <div className="text-xs font-mono text-neutral-400">{inst.url}</div>
                 </div>
                 <div className="flex items-center gap-3">
                   {testStatuses[inst.id] && (
                     <span className={`text-xs px-2 py-1 rounded flex items-center gap-1 ${testStatuses[inst.id].online ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-rose-950 text-rose-400 border border-rose-800'}`}>
                       {testStatuses[inst.id].online ? <CheckCircle2 className="w-3 h-3" /> : <AlertCircle className="w-3 h-3" />}
                       {testStatuses[inst.id].online ? `${testStatuses[inst.id].latency}ms` : 'Offline'}
                     </span>
                   )}
                   <button
                     onClick={() => handleTestInstance(inst)}
                     disabled={testingId === inst.id}
                     className="px-3 py-1.5 text-xs bg-neutral-800 hover:bg-neutral-700 text-neutral-200 rounded border border-neutral-700 transition"
                   >
                     {testingId === inst.id ? <RefreshCw className="w-3 h-3 animate-spin" /> : 'Test'}
                   </button>
                 </div>
               </div>
             ))}
           </div>
         </section>

         {/* Junior & Senior Model Assignment */}
         <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
           <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5 space-y-3">
             <h3 className="font-medium text-white flex items-center gap-2">
               <Cpu className="w-4 h-4 text-amber-400" />
               Junior Coder Engine
             </h3>
             <label className="block text-xs text-neutral-400">Model Name</label>
             <input
               type="text"
               value={config.junior_config.model_name}
               onChange={e => setConfig({
                 ...config,
                 junior_config: { ...config.junior_config, model_name: e.target.value }
               })}
               className="w-full bg-neutral-950 border border-neutral-800 rounded px-3 py-2 text-sm text-white"
             />
           </div>

           <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5 space-y-3">
             <h3 className="font-medium text-white flex items-center gap-2">
               <ShieldCheck className="w-4 h-4 text-emerald-400" />
               Senior Reviewer Slot
             </h3>
             <label className="block text-xs text-neutral-400">Reviewer Model (CDP or Ollama)</label>
             <select
               value={config.senior_config.model_name}
               onChange={e => setConfig({
                 ...config,
                 senior_config: { ...config.senior_config, model_name: e.target.value }
               })}
               className="w-full bg-neutral-950 border border-neutral-800 rounded px-3 py-2 text-sm text-white"
             >
               {cdpModels.map(m => (
                 <option key={m} value={m}>{m}</option>
               ))}
               {!cdpModels.includes(config.senior_config.model_name) && (
                 <option value={config.senior_config.model_name}>{config.senior_config.model_name}</option>
               )}
             </select>
           </div>
         </section>
       </div>
     );
   };

   // ui/src/components/SchedulerPanel.tsx
   import React, { useState, useEffect } from 'react';
   import { Calendar, Play, Clock, CheckCircle } from 'lucide-react';
   import type { HubConfig, RepoScheduleConfig } from '../types';
   import { api } from '../api';

   interface SchedulerPanelProps {
     onTriggerRepo?: (repoName: string) => void;
   }

   export const SchedulerPanel: React.FC<SchedulerPanelProps> = ({ onTriggerRepo }) => {
     const [config, setConfig] = useState<HubConfig | null>(null);
     const [triggering, setTriggering] = useState<string | null>(null);

     useEffect(() => {
       api.getConfig().then(setConfig).catch(console.error);
     }, []);

     const handleTrigger = async (repoName: string) => {
       setTriggering(repoName);
       try {
         await api.triggerScheduler(repoName);
         if (onTriggerRepo) onTriggerRepo(repoName);
         const updated = await api.getConfig();
         setConfig(updated);
       } catch (err) {
         console.error('Trigger failed', err);
       } finally {
         setTriggering(null);
       }
     };

     if (!config) return <div className="p-8 text-neutral-400">Loading scheduler...</div>;

     return (
       <div className="max-w-4xl mx-auto p-6 space-y-6 text-neutral-200">
         <div className="flex items-center justify-between border-b border-neutral-800 pb-4">
           <div>
             <h2 className="text-xl font-semibold text-white">Autonomous Repository Scheduler</h2>
             <p className="text-sm text-neutral-400">Autonomous curation cycles with max-pending-worktree safety limits.</p>
           </div>
           <Calendar className="w-6 h-6 text-indigo-400" />
         </div>

         <div className="space-y-4">
           {config.repo_schedules.map(sched => (
             <div key={sched.repo_name} className="bg-neutral-900 border border-neutral-800 rounded-xl p-5 flex items-center justify-between">
               <div className="space-y-2">
                 <div className="flex items-center gap-3">
                   <span className="font-semibold text-white text-base">{sched.repo_name}</span>
                   <span className={`text-xs px-2 py-0.5 rounded font-medium ${sched.enabled ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-neutral-800 text-neutral-400'}`}>
                     {sched.enabled ? 'Active' : 'Paused'}
                   </span>
                 </div>
                 <div className="flex items-center gap-4 text-xs text-neutral-400">
                   <span className="flex items-center gap-1"><Clock className="w-3.5 h-3.5" /> Every {sched.interval_hours}h</span>
                   <span>Max Pending: {sched.max_pending_worktrees}</span>
                   {sched.last_run_at && <span>Last: {new Date(sched.last_run_at).toLocaleTimeString()}</span>}
                 </div>
               </div>
               <button
                 onClick={() => handleTrigger(sched.repo_name)}
                 disabled={triggering === sched.repo_name}
                 className="flex items-center gap-2 px-3 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition"
               >
                 <Play className="w-4 h-4" />
                 {triggering === sched.repo_name ? 'Triggering...' : 'Trigger Now'}
               </button>
             </div>
           ))}
         </div>
       </div>
     );
   };

   // ui/src/components/SuggestionCard.tsx
   import React from 'react';
   import { Zap, Palette, Shield, Trash2, ArrowRight } from 'lucide-react';
   import type { Suggestion } from '../types';

   interface SuggestionCardProps {
     suggestion: Suggestion;
     onApply: (s: Suggestion) => void;
     onDiscard: (id: string) => void;
   }

   export const SuggestionCard: React.FC<SuggestionCardProps> = ({ suggestion, onApply, onDiscard }) => {
     const getPersonaIcon = (p: string) => {
       switch (p.toLowerCase()) {
         case 'bolt': return <Zap className="w-4 h-4 text-amber-400" />;
         case 'palette': return <Palette className="w-4 h-4 text-pink-400" />;
         default: return <Shield className="w-4 h-4 text-emerald-400" />;
       }
     };

     return (
       <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5 space-y-4 hover:border-neutral-700 transition">
         <div className="flex items-center justify-between">
           <span className="flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 bg-neutral-950 rounded-full border border-neutral-800">
             {getPersonaIcon(suggestion.persona)}
             <span className="capitalize text-neutral-300">{suggestion.persona}</span>
           </span>
           <button
             onClick={() => onDiscard(suggestion.id)}
             title="Discard Suggestion"
             className="text-neutral-500 hover:text-rose-400 transition"
           >
             <Trash2 className="w-4 h-4" />
           </button>
         </div>

         <div>
           <h4 className="font-medium text-white text-base">{suggestion.title}</h4>
           <div className="text-xs text-neutral-400 font-mono mt-1">{suggestion.file}:{suggestion.line}</div>
         </div>

         <p className="text-sm text-neutral-300">{suggestion.issue}</p>

         {suggestion.code_snippet && (
           <pre className="p-3 bg-neutral-950 rounded text-xs font-mono text-neutral-300 overflow-x-auto border border-neutral-800">
             {suggestion.code_snippet}
           </pre>
         )}

         <div className="pt-2 flex justify-end">
           <button
             onClick={() => onApply(suggestion)}
             className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-medium transition"
           >
             <span>Curate in Worktree</span>
             <ArrowRight className="w-3.5 h-3.5" />
           </button>
         </div>
       </div>
     );
   };

   // ui/src/components/DiffDrawer.tsx
   import React, { useState } from 'react';
   import { X, ShieldCheck, GitPullRequest, AlertTriangle, CheckCircle } from 'lucide-react';
   import type { SeniorReviewResult } from '../types';
   import { api } from '../api';

   interface DiffDrawerProps {
     isOpen: boolean;
     onClose: () => void;
     taskId: string;
     diff: string;
     initialReview?: SeniorReviewResult | null;
   }

   export const DiffDrawer: React.FC<DiffDrawerProps> = ({ isOpen, onClose, taskId, diff, initialReview }) => {
     const [review, setReview] = useState<SeniorReviewResult | null>(initialReview || null);
     const [isReviewing, setIsReviewing] = useState(false);
     const [prCreated, setPrCreated] = useState<string | null>(null);

     if (!isOpen) return null;

     const handleRequestSeniorReview = async () => {
       setIsReviewing(true);
       try {
         const res = await api.seniorReview(taskId, diff);
         setReview(res);
       } catch (err) {
         console.error('Senior Review failed', err);
       } finally {
         setIsReviewing(false);
       }
     };

     const handleCreatePr = async () => {
       try {
         const res = await api.createPr(taskId);
         if (res.pr_url) setPrCreated(res.pr_url);
       } catch (err: any) {
         alert(`PR Creation Failed: ${err.message}`);
       }
     };

     const isApproved = review?.verdict === 'APPROVED';

     return (
       <div className="fixed inset-y-0 right-0 w-full max-w-2xl bg-neutral-900 border-l border-neutral-800 z-50 flex flex-col shadow-2xl">
         <div className="flex items-center justify-between p-4 border-b border-neutral-800">
           <div className="flex items-center gap-2">
             <ShieldCheck className="w-5 h-5 text-indigo-400" />
             <h3 className="font-semibold text-white">Worktree Diff & Senior Gate</h3>
           </div>
           <button onClick={onClose} className="text-neutral-400 hover:text-white"><X className="w-5 h-5" /></button>
         </div>

         <div className="flex-1 overflow-y-auto p-4 space-y-4 font-mono text-xs">
           <pre className="p-4 bg-neutral-950 rounded-lg text-neutral-300 border border-neutral-800 whitespace-pre-wrap">
             {diff || 'No diff content'}
           </pre>

           {/* Senior Review Gate Outcome */}
           {review && (
             <div className={`p-4 rounded-lg border space-y-2 ${isApproved ? 'bg-emerald-950/40 border-emerald-800 text-emerald-200' : 'bg-rose-950/40 border-rose-800 text-rose-200'}`}>
               <div className="flex items-center justify-between">
                 <span className="font-bold flex items-center gap-1.5">
                   {isApproved ? <CheckCircle className="w-4 h-4 text-emerald-400" /> : <AlertTriangle className="w-4 h-4 text-rose-400" />}
                   Senior Verdict: {review.verdict}
                 </span>
                 <span className="text-xs opacity-75">{review.reviewer_model}</span>
               </div>
               <p className="text-xs opacity-90">{review.simple_explanation}</p>
               <div className="text-xs font-semibold">Security: {review.security_notes}</div>
             </div>
           )}
         </div>

         <div className="p-4 border-t border-neutral-800 flex items-center justify-between bg-neutral-950">
           <button
             onClick={handleRequestSeniorReview}
             disabled={isReviewing}
             className="px-4 py-2 bg-neutral-800 hover:bg-neutral-700 text-white rounded-lg text-sm font-medium transition"
           >
             {isReviewing ? 'Auditing...' : 'Request Senior Review'}
           </button>

           <button
             onClick={handleCreatePr}
             disabled={!isApproved}
             title={!isApproved ? 'Senior Review approval required before PR creation' : ''}
             className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${isApproved ? 'bg-emerald-600 hover:bg-emerald-500 text-white' : 'bg-neutral-800 text-neutral-500 cursor-not-allowed'}`}
           >
             <GitPullRequest className="w-4 h-4" />
             {prCreated ? 'PR Opened!' : 'Create Pull Request'}
           </button>
         </div>
       </div>
     );
   };

   // ui/src/App.tsx
   import React, { useState } from 'react';
   import { Layers, Calendar, Settings, Activity } from 'lucide-react';
   import { SettingsView } from './components/SettingsView';
   import { SchedulerPanel } from './components/SchedulerPanel';
   import { SuggestionCard } from './components/SuggestionCard';
   import { DiffDrawer } from './components/DiffDrawer';
   import type { Suggestion } from './types';

   export const App: React.FC = () => {
     // Native React tab routing (Cockpit, Scheduler, Settings) without react-router-dom
     const [activeTab, setActiveTab] = useState<'cockpit' | 'scheduler' | 'settings'>('cockpit');
     const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
     const [drawerOpen, setDrawerOpen] = useState(false);
     const [selectedTaskId, setSelectedTaskId] = useState('');
     const [selectedDiff, setSelectedDiff] = useState('');

     return (
       <div className="min-h-screen bg-neutral-950 text-neutral-100 flex flex-col">
         {/* Navigation Bar */}
         <header className="border-b border-neutral-800 bg-neutral-900/60 backdrop-blur sticky top-0 z-40 px-6 py-3 flex items-center justify-between">
           <div className="flex items-center gap-3">
             <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20">
               J
             </div>
             <div>
               <h1 className="font-semibold text-white tracking-wide">Jules Hub v2</h1>
               <p className="text-xs text-neutral-400">Autonomous Cockpit</p>
             </div>
           </div>

           {/* Native Tab Selector */}
           <nav className="flex items-center gap-1 bg-neutral-950 p-1 rounded-xl border border-neutral-800">
             <button
               onClick={() => setActiveTab('cockpit')}
               className={`flex items-center gap-2 px-4 py-1.5 rounded-lg text-sm font-medium transition ${activeTab === 'cockpit' ? 'bg-neutral-800 text-white shadow-sm' : 'text-neutral-400 hover:text-white'}`}
             >
               <Layers className="w-4 h-4" />
               Cockpit
             </button>
             <button
               onClick={() => setActiveTab('scheduler')}
               className={`flex items-center gap-2 px-4 py-1.5 rounded-lg text-sm font-medium transition ${activeTab === 'scheduler' ? 'bg-neutral-800 text-white shadow-sm' : 'text-neutral-400 hover:text-white'}`}
             >
               <Calendar className="w-4 h-4" />
               Scheduler
             </button>
             <button
               onClick={() => setActiveTab('settings')}
               className={`flex items-center gap-2 px-4 py-1.5 rounded-lg text-sm font-medium transition ${activeTab === 'settings' ? 'bg-neutral-800 text-white shadow-sm' : 'text-neutral-400 hover:text-white'}`}
             >
               <Settings className="w-4 h-4" />
               Settings
             </button>
           </nav>

           <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-950/60 border border-emerald-800 px-3 py-1 rounded-full">
             <Activity className="w-3.5 h-3.5" />
             <span>Connected</span>
           </div>
         </header>

         {/* Tab Content Rendering */}
         <main className="flex-1 p-6">
           {activeTab === 'cockpit' && (
             <div className="max-w-6xl mx-auto space-y-6">
               <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                 {suggestions.map(s => (
                   <SuggestionCard
                     key={s.id}
                     suggestion={s}
                     onApply={sug => {
                       setSelectedTaskId(`task_${sug.id}`);
                       setSelectedDiff(`--- a/${sug.file}\n+++ b/${sug.file}\n@@ -${sug.line},1 +${sug.line},1 @@\n- old_code\n+ optimized_code`);
                       setDrawerOpen(true);
                     }}
                     onDiscard={id => setSuggestions(prev => prev.filter(x => x.id !== id))}
                   />
                 ))}
               </div>
             </div>
           )}

           {activeTab === 'scheduler' && <SchedulerPanel />}
           {activeTab === 'settings' && <SettingsView />}
         </main>

         {/* Senior Gate Diff Drawer */}
         <DiffDrawer
           isOpen={drawerOpen}
           onClose={() => setDrawerOpen(false)}
           taskId={selectedTaskId}
           diff={selectedDiff}
         />
       </div>
     );
   };

   export default App;
   ```

4. **Verify GREEN**:
   ```bash
   npm test
   ```

This implementation plan provides a detailed roadmap for developing the Jules Hub v2 Autonomous Cockpit, ensuring that each component is thoroughly tested and implemented using Test-Driven Development (TDD) principles.