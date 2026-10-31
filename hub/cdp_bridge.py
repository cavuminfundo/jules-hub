"""
Antigravity Chrome DevTools Protocol (CDP) Escalation Bridge.
Connects to Antigravity Desktop via CDP port 9000 to trigger Senior Review.
Resilient against closed port, timeout, and connection errors without raising exceptions.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union

import httpx
from pydantic import BaseModel, ConfigDict
import websockets

import hub.models
from hub.models import CDPResponse as BaseCDPResponse, EscalateRequest

logger = logging.getLogger("hub.cdp_bridge")

DEFAULT_CDP_HOST = os.environ.get("CDP_HOST", "127.0.0.1")
DEFAULT_CDP_PORT = int(os.environ.get("CDP_PORT", "9000"))


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
