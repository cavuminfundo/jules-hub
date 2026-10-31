"""
Unit tests for Antigravity CDP Escalation Bridge (hub/cdp_bridge.py).
Tests handshake with /json/list, target selection, WebSocket command dispatch,
and error handling (connection refused, timeouts, discovery failure).
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
import pytest
import websockets

from hub.cdp_bridge import CDPBridge, CDPResponse
from hub.models import EscalateRequest


@pytest.fixture
def sample_req():
    return EscalateRequest(
        repo="jules-hub",
        worktree_path="/home/federico/jules/worktrees/jules-hub-bolt-1",
        branch="curator/bolt-20261031-1530",
        diff_summary="Optimize database query batching (< 20 lines)",
        test_status="PASSED (14 fast tests green)",
        instruction="Esegui audit Senior. Se approvato, apri la PR su GitHub.",
    )


def test_cdp_bridge_init():
    """Verify initialization defaults and properties."""
    bridge = CDPBridge()
    assert bridge.cdp_host == "127.0.0.1"
    assert bridge.cdp_port == 9000
    assert bridge.timeout == 5.0
    assert bridge.http_base_url == "http://127.0.0.1:9000"

    custom = CDPBridge(cdp_host="192.168.1.50", cdp_port=9222, timeout=2.5)
    assert custom.cdp_host == "192.168.1.50"
    assert custom.cdp_port == 9222
    assert custom.timeout == 2.5
    assert custom.http_base_url == "http://192.168.1.50:9222"


@pytest.mark.asyncio
async def test_get_debugger_url_page_target():
    """Verify selection of page type target with webSocketDebuggerUrl."""
    bridge = CDPBridge()
    targets = [
        {"type": "service_worker", "title": "Worker", "webSocketDebuggerUrl": "ws://127.0.0.1:9000/sw"},
        {"type": "page", "title": "Antigravity Main", "webSocketDebuggerUrl": "ws://127.0.0.1:9000/devtools/page/page1"},
    ]

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = targets

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        ws_url, err = await bridge.get_debugger_url()
        assert ws_url == "ws://127.0.0.1:9000/devtools/page/page1"
        assert err is None


@pytest.mark.asyncio
async def test_get_debugger_url_fallback_target():
    """Verify fallback when no page target exists but debugger URL is present."""
    bridge = CDPBridge()
    targets = [
        {"type": "other", "title": "Window", "webSocketDebuggerUrl": "ws://127.0.0.1:9000/devtools/fallback/1"},
    ]

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = targets

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        ws_url, err = await bridge.get_debugger_url()
        assert ws_url == "ws://127.0.0.1:9000/devtools/fallback/1"
        assert err is None


@pytest.mark.asyncio
async def test_get_debugger_url_empty_targets():
    """Verify error handling when /json/list returns an empty list."""
    bridge = CDPBridge()
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = []

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        ws_url, err = await bridge.get_debugger_url()
        assert ws_url is None
        assert "No active CDP targets found" in err


@pytest.mark.asyncio
async def test_get_debugger_url_missing_ws_url():
    """Verify error handling when targets have no webSocketDebuggerUrl."""
    bridge = CDPBridge()
    targets = [{"type": "page", "title": "Page Without WS"}]
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = targets

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        ws_url, err = await bridge.get_debugger_url()
        assert ws_url is None
        assert "No webSocketDebuggerUrl found" in err


@pytest.mark.asyncio
async def test_get_debugger_url_http_error():
    """Verify error handling when CDP endpoint returns non-200 status."""
    bridge = CDPBridge()
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 502
    mock_resp.text = "Bad Gateway"

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        ws_url, err = await bridge.get_debugger_url()
        assert ws_url is None
        assert "HTTP 502" in err


@pytest.mark.asyncio
async def test_get_debugger_url_connection_refused():
    """Verify resilient handling when port 9000 is closed."""
    bridge = CDPBridge()
    with patch("httpx.AsyncClient.get", side_effect=httpx.ConnectError("Connection refused")):
        ws_url, err = await bridge.get_debugger_url()
        assert ws_url is None
        assert "connection refused" in err.lower()


@pytest.mark.asyncio
async def test_get_debugger_url_timeout():
    """Verify resilient handling when discovery times out."""
    bridge = CDPBridge()
    with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("Read timed out")):
        ws_url, err = await bridge.get_debugger_url()
        assert ws_url is None
        assert "timeout" in err.lower()


@pytest.mark.asyncio
async def test_escalate_to_antigravity_success(sample_req):
    """Verify successful escalation via CDP Runtime.evaluate."""
    bridge = CDPBridge()
    ws_url = "ws://127.0.0.1:9000/devtools/page/test1"

    sent_messages = []

    class MockWebSocket:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        async def send(self, data: str):
            sent_messages.append(data)

        async def recv(self):
            return json.dumps({
                "id": 1,
                "result": {
                    "result": {
                        "type": "string",
                        "value": "Review acknowledged by Antigravity Desktop",
                    }
                }
            })

    with patch.object(bridge, "get_debugger_url", new_callable=AsyncMock) as mock_get_url:
        mock_get_url.return_value = (ws_url, None)
        with patch("websockets.connect", return_value=MockWebSocket()):
            resp = await bridge.escalate_to_antigravity(sample_req)

            assert isinstance(resp, CDPResponse)
            assert resp.success is True
            assert resp.error is None
            assert "successfully" in resp.message.lower()
            assert resp.response_data is not None

            # Verify command sent to WebSocket
            assert len(sent_messages) == 1
            cmd = json.loads(sent_messages[0])
            assert cmd["method"] == "Runtime.evaluate"
            assert "params" in cmd
            assert sample_req.repo in cmd["params"]["expression"]
            assert sample_req.branch in cmd["params"]["expression"]


@pytest.mark.asyncio
async def test_escalate_to_antigravity_port_closed(sample_req):
    """Verify graceful failure when port 9000 is closed (no 500 error, no crash)."""
    bridge = CDPBridge()
    with patch.object(bridge, "get_debugger_url", new_callable=AsyncMock) as mock_get_url:
        mock_get_url.return_value = (None, "CDP connection refused on 127.0.0.1:9000: Connection refused")
        resp = await bridge.escalate_to_antigravity(sample_req)

        assert isinstance(resp, CDPResponse)
        assert resp.success is False
        assert "connection refused" in resp.message.lower()
        assert resp.error is not None
        assert "connection refused" in resp.error.lower()


@pytest.mark.asyncio
async def test_escalate_to_antigravity_ws_connect_error(sample_req):
    """Verify graceful handling when HTTP handshake succeeds but WebSocket connection fails."""
    bridge = CDPBridge()
    ws_url = "ws://127.0.0.1:9000/devtools/page/test1"

    with patch.object(bridge, "get_debugger_url", new_callable=AsyncMock) as mock_get_url:
        mock_get_url.return_value = (ws_url, None)
        with patch("websockets.connect", side_effect=websockets.exceptions.WebSocketException("Handshake failed")):
            resp = await bridge.escalate_to_antigravity(sample_req)

            assert isinstance(resp, CDPResponse)
            assert resp.success is False
            assert "WebSocket connection failed" in resp.message
            assert resp.error is not None


@pytest.mark.asyncio
async def test_escalate_to_antigravity_ws_timeout(sample_req):
    """Verify graceful handling when WebSocket response times out."""
    bridge = CDPBridge()
    ws_url = "ws://127.0.0.1:9000/devtools/page/test1"

    class TimeoutWebSocket:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        async def send(self, data: str):
            pass

        async def recv(self):
            raise asyncio.TimeoutError()

    with patch.object(bridge, "get_debugger_url", new_callable=AsyncMock) as mock_get_url:
        mock_get_url.return_value = (ws_url, None)
        with patch("websockets.connect", return_value=TimeoutWebSocket()):
            resp = await bridge.escalate_to_antigravity(sample_req)

            assert isinstance(resp, CDPResponse)
            assert resp.success is False
            assert "timed out" in resp.message.lower()
            assert "timed out" in resp.error.lower()


@pytest.mark.asyncio
async def test_escalate_to_antigravity_cdp_error_payload(sample_req):
    """Verify handling when CDP evaluates to an error response."""
    bridge = CDPBridge()
    ws_url = "ws://127.0.0.1:9000/devtools/page/test1"

    class ErrorWebSocket:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        async def send(self, data: str):
            pass

        async def recv(self):
            return json.dumps({
                "id": 1,
                "error": {
                    "code": -32000,
                    "message": "Execution context was destroyed",
                }
            })

    with patch.object(bridge, "get_debugger_url", new_callable=AsyncMock) as mock_get_url:
        mock_get_url.return_value = (ws_url, None)
        with patch("websockets.connect", return_value=ErrorWebSocket()):
            resp = await bridge.escalate_to_antigravity(sample_req)

            assert isinstance(resp, CDPResponse)
            assert resp.success is False
            assert "Execution context was destroyed" in resp.message
            assert "Execution context was destroyed" in resp.error
