"""
Antigravity Chrome DevTools Protocol (CDP) Escalation Bridge.
Connects to Antigravity Desktop via CDP port 9000 to trigger Senior Review.
Resilient against closed port, timeout, and connection errors without raising exceptions.
"""

import asyncio
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple, Union

import httpx
from pydantic import BaseModel, ConfigDict
import websockets

import hub.models
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
    """CDP response with explicit error field support."""
    model_config = ConfigDict(extra="ignore")

    error: Optional[str] = None


class CDPBridge:
    """
    Bridge to Antigravity Desktop via Chrome DevTools Protocol (CDP).
    Default target is 127.0.0.1:9000.
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
        """
        Query http://{cdp_host}:{cdp_port}/json/list to find the target webSocketDebuggerUrl.
        Returns (ws_url, error_message).
        """
        url = f"{self.http_base_url}/json/list"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return None, f"CDP endpoint returned HTTP {resp.status_code}: {resp.text[:100]}"
                targets = resp.json()
        except (httpx.ConnectError, ConnectionRefusedError, OSError) as e:
            return None, f"CDP connection refused on {self.cdp_host}:{self.cdp_port}: {e}"
        except (httpx.TimeoutException, asyncio.TimeoutError) as e:
            return None, f"CDP connection timeout on {self.cdp_host}:{self.cdp_port}: {e}"
        except Exception as e:
            return None, f"CDP discovery error on {url}: {e}"

        if not isinstance(targets, list) or len(targets) == 0:
            return None, f"No active CDP targets found on {self.http_base_url}/json/list"

        # Prioritize 'page' target
        for t in targets:
            if isinstance(t, dict) and t.get("type") == "page" and "webSocketDebuggerUrl" in t:
                return t["webSocketDebuggerUrl"], None

        # Fallback to any target with a debugger URL
        for t in targets:
            if isinstance(t, dict) and "webSocketDebuggerUrl" in t:
                return t["webSocketDebuggerUrl"], None

        return None, f"No webSocketDebuggerUrl found in CDP target list ({len(targets)} targets)"

    async def escalate_to_antigravity(self, req: EscalateRequest) -> CDPResponse:
        """
        Escalate a worktree review request to Antigravity Desktop via CDP Runtime.evaluate.
        Never raises exceptions; captures connection errors and timeouts cleanly.
        """
        ws_url, err = await self.get_debugger_url()
        if not ws_url or err:
            logger.warning("CDP discovery failed: %s", err)
            return CDPResponse(
                success=False,
                message=err or "CDP discovery failed",
                error=err or "CDP discovery failed",
            )

        payload = {
            "action": "senior_review",
            "repo": req.repo,
            "worktree_path": req.worktree_path,
            "branch": req.branch,
            "diff_summary": req.diff_summary,
            "test_status": req.test_status,
            "instruction": req.instruction,
        }

        # CDP Runtime.evaluate command payload
        cdp_cmd = {
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {
                "expression": (
                    f"window.triggerSeniorReview ? "
                    f"window.triggerSeniorReview({json.dumps(payload)}) : "
                    f"console.log('Antigravity Senior Review Triggered', {json.dumps(payload)});"
                ),
                "returnByValue": True,
                "awaitPromise": True,
            },
        }

        try:
            # Connect via websockets
            async with websockets.connect(
                ws_url,
                open_timeout=self.timeout,
                close_timeout=self.timeout,
            ) as ws:
                await ws.send(json.dumps(cdp_cmd))
                raw_response = await asyncio.wait_for(ws.recv(), timeout=self.timeout)
                resp_data = json.loads(raw_response)

                if "error" in resp_data:
                    err_msg = f"CDP Runtime.evaluate returned error: {resp_data['error']}"
                    return CDPResponse(
                        success=False,
                        message=err_msg,
                        error=err_msg,
                        response_data=resp_data,
                    )

                return CDPResponse(
                    success=True,
                    message=f"Escalated senior review for {req.repo} ({req.branch}) successfully",
                    error=None,
                    response_data=resp_data,
                )

        except (asyncio.TimeoutError, TimeoutError) as e:
            logger.warning("Timeout during CDP communication with %s", ws_url)
            detail = f": {e}" if str(e) else ""
            err_msg = f"CDP WebSocket communication timed out after {self.timeout}s{detail}"
            return CDPResponse(success=False, message=err_msg, error=err_msg)
        except (websockets.exceptions.WebSocketException, ConnectionRefusedError, OSError) as e:
            logger.warning("WebSocket error connecting to %s: %s", ws_url, e)
            err_msg = f"CDP WebSocket connection failed on {ws_url}: {e}"
            return CDPResponse(success=False, message=err_msg, error=err_msg)
        except Exception as e:
            logger.error("Unexpected error during CDP escalation: %s", e)
            err_msg = f"Unexpected CDP error: {e}"
            return CDPResponse(success=False, message=err_msg, error=err_msg)

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

