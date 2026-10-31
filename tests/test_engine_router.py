"""
Unit tests for Jules Hub Multi-Engine Router (hub/engine_router.py).
Tests Ollama local HTTP client, Antigravity Flash CLI runner, Hybrid mode,
graceful fallbacks, process group kills on timeout, and path traversal guards.
"""

import asyncio
import json
import os
import signal
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import httpx

from hub.engine_router import (
    EngineRouter,
    count_diff_lines,
    extract_diff_from_text,
    extract_code_from_text,
    apply_hunks_to_content,
)
from hub.models import EngineMode, PatchResult, PERSONAS


# ---------------------------------------------------------------------------
# Unit tests for helper functions
# ---------------------------------------------------------------------------

def test_count_diff_lines():
    diff_text = (
        "--- a/sample.py\n"
        "+++ b/sample.py\n"
        "@@ -1,5 +1,6 @@\n"
        " def foo():\n"
        "-    old_call()\n"
        "-    unneeded()\n"
        "+    new_optimized_call()\n"
        "+    another_line()\n"
        "+    third_line()\n"
        "     return True\n"
    )
    # 2 deleted + 3 added = 5 lines changed
    assert count_diff_lines(diff_text) == 5


def test_count_diff_lines_ignores_headers():
    diff_text = (
        "--- a/file.py\n"
        "+++ b/file.py\n"
        "@@ -1 +1 @@\n"
        "-x = 1\n"
        "+x = 2\n"
    )
    assert count_diff_lines(diff_text) == 2


def test_count_diff_lines_escaped_newlines():
    diff_escaped = "--- a/file.py\\n+++ b/file.py\\n@@ -1 +1 @@\\n-x = 1\\n+x = 2\\n"
    assert count_diff_lines(diff_escaped) == 2


def test_extract_diff_from_markdown():
    text = (
        "Here is the solution to your issue:\n\n"
        "```diff\n"
        "--- a/test.py\n"
        "+++ b/test.py\n"
        "@@ -1,2 +1,2 @@\n"
        "-bad()\n"
        "+good()\n"
        "```\n\n"
        "Hope this helps!"
    )
    diff = extract_diff_from_text(text)
    assert diff is not None
    assert "--- a/test.py" in diff
    assert "+good()" in diff


def test_extract_code_from_markdown():
    text = (
        "Updated file contents:\n"
        "```python\n"
        "def hello():\n"
        "    return 'world'\n"
        "```\n"
    )
    code = extract_code_from_text(text)
    assert code is not None
    assert "def hello():" in code


def test_apply_hunks_to_content():
    orig = "line 1\nline 2\nline 3\n"
    diff = (
        "--- a/sample.txt\n"
        "+++ b/sample.txt\n"
        "@@ -1,3 +1,3 @@\n"
        " line 1\n"
        "-line 2\n"
        "+line 2 modified\n"
        " line 3\n"
    )
    result = apply_hunks_to_content(orig, diff)
    assert result is not None
    assert "line 2 modified" in result
    assert "line 1" in result


# ---------------------------------------------------------------------------
# Router initialization & parameter tests
# ---------------------------------------------------------------------------

def test_engine_router_defaults():
    router = EngineRouter()
    assert router.ollama_url == "http://localhost:11434"
    assert router.ollama_model == "qwen2.5-coder"
    assert router.agy_bin == "agy"
    assert router.default_mode == EngineMode.ANTIGRAVITY_FLASH
    assert router.max_lines == 50
    assert router.http_timeout == 60.0
    assert router.subprocess_timeout == 120.0
    assert router.allow_fallback is True


def test_engine_router_env_overrides(monkeypatch):
    monkeypatch.setenv("OLLAMA_HOST", "http://custom-ollama:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "deepseek-coder:6.7b")
    monkeypatch.setenv("AGY_BIN", "/custom/bin/agy")

    router = EngineRouter()
    assert router.ollama_url == "http://custom-ollama:11434"
    assert router.ollama_model == "deepseek-coder:6.7b"
    assert router.agy_bin == "/custom/bin/agy"


# ---------------------------------------------------------------------------
# Mode: Local (Ollama httpx)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mode_local_success(tmp_path: Path):
    """Verify Local mode executes httpx request to Ollama and applies unified diff."""
    target = tmp_path / "service.py"
    target.write_text("def fetch_data():\n    db.query_all()\n", encoding="utf-8")

    diff_payload = (
        "```diff\n"
        "--- a/service.py\n"
        "+++ b/service.py\n"
        "@@ -1,2 +1,2 @@\n"
        " def fetch_data():\n"
        "-    db.query_all()\n"
        "+    db.query_batch()\n"
        "```"
    )

    router = EngineRouter(ollama_url="http://localhost:11434", ollama_model="qwen2.5-coder")

    # Mock httpx.AsyncClient post
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {"model": "qwen2.5-coder", "response": diff_payload, "done": True}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        res = await router.analyze_and_patch(
            repo_path=tmp_path,
            persona="bolt",
            target_file="service.py",
            issue_context="N+1 query problem detected in fetch_data",
            mode=EngineMode.LOCAL,
        )

        assert isinstance(res, PatchResult)
        assert res.success is True
        assert res.engine_used == "local"
        assert res.diff is not None
        assert "db.query_batch()" in res.diff
        assert res.lines_changed == 2
        assert res.error is None

        # Verify POST target endpoint and payload
        mock_post.assert_awaited_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "http://localhost:11434/api/generate"
        assert kwargs["json"]["model"] == "qwen2.5-coder"
        assert "bolt" in kwargs["json"]["prompt"].lower()
        assert "query_all" in kwargs["json"]["prompt"]

        # Verify target file was patched
        updated_content = target.read_text(encoding="utf-8")
        assert "db.query_batch()" in updated_content


@pytest.mark.asyncio
async def test_mode_local_failure_returns_patch_result_without_exception(tmp_path: Path):
    """When Local Ollama fails (e.g. connection refused), return PatchResult with error without raising."""
    target = tmp_path / "service.py"
    target.write_text("x = 1\n", encoding="utf-8")

    router = EngineRouter()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.ConnectError("Connection refused to http://localhost:11434")

        res = await router.analyze_and_patch(
            repo_path=tmp_path,
            persona="sentinel",
            target_file="service.py",
            issue_context="Hardcoded credential",
            mode=EngineMode.LOCAL,
        )

        # Invariant: NO unhandled exception raised
        assert isinstance(res, PatchResult)
        assert res.success is False
        assert res.engine_used == "local"
        assert res.diff is None
        assert "Connection refused" in res.error or "failed" in res.error.lower()


# ---------------------------------------------------------------------------
# Mode: Antigravity Flash (agy CLI runner)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mode_antigravity_flash_success(tmp_path: Path):
    """Verify Flash mode executes headless runner via typed list[str] arguments and shell=False."""
    target = tmp_path / "button.tsx"
    target.write_text("<button onClick={handleClick}><Icon /></button>\n", encoding="utf-8")

    diff_output = (
        "--- a/button.tsx\n"
        "+++ b/button.tsx\n"
        "@@ -1 +1 @@\n"
        "-<button onClick={handleClick}><Icon /></button>\n"
        "+<button onClick={handleClick} aria-label=\"Action\"><Icon /></button>\n"
    )

    ndjson_stream = (
        json.dumps({"type": "message", "role": "assistant", "content": "Adding aria-label"}) + "\n"
        + json.dumps({"type": "result", "diff": diff_output}) + "\n"
    )

    router = EngineRouter()

    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.communicate = AsyncMock(return_value=(ndjson_stream.encode("utf-8"), b""))

    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = mock_proc

        res = await router.analyze_and_patch(
            repo_path=tmp_path,
            persona="palette",
            target_file="button.tsx",
            issue_context="Missing ARIA label on icon-only button",
            mode=EngineMode.ANTIGRAVITY_FLASH,
        )

        assert isinstance(res, PatchResult)
        assert res.success is True
        assert res.engine_used == "antigravity_flash"
        assert res.diff is not None
        assert "aria-label" in res.diff
        assert res.lines_changed == 2

        # Invariant: Typed argument list (list[str]) starting with required flags
        mock_exec.assert_awaited_once()
        cmd_args, kwargs = mock_exec.call_args
        assert cmd_args[0] == "agy"
        assert list(cmd_args[1:7]) == ["--model", "flash", "--mode", "auto", "--output-format", "stream-json"]
        assert all(isinstance(arg, str) for arg in cmd_args)
        assert kwargs["cwd"] == str(tmp_path.resolve())
        assert kwargs["preexec_fn"] == os.setsid


# ---------------------------------------------------------------------------
# Fallback Mechanism Tests (Flash -> Local -> Structured Error)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fallback_when_flash_fails_degrades_to_local(tmp_path: Path):
    """When Flash fails (e.g. process crash or non-zero exit), degrades gracefully to local Ollama."""
    target = tmp_path / "app.py"
    target.write_text("def run():\n    return False\n", encoding="utf-8")

    diff_payload = (
        "```diff\n"
        "--- a/app.py\n"
        "+++ b/app.py\n"
        "@@ -1,2 +1,2 @@\n"
        " def run():\n"
        "-    return False\n"
        "+    return True\n"
        "```"
    )

    router = EngineRouter(allow_fallback=True)

    # 1. Flash runner fails with non-zero exit code
    mock_flash_proc = MagicMock()
    mock_flash_proc.returncode = 1
    mock_flash_proc.communicate = AsyncMock(return_value=(b"", b"Error: agy quota exceeded or crashed"))

    # 2. Local Ollama succeeds
    mock_ollama_resp = MagicMock(spec=httpx.Response)
    mock_ollama_resp.status_code = 200
    mock_ollama_resp.json.return_value = {"response": diff_payload}
    mock_ollama_resp.raise_for_status = MagicMock()

    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:

        mock_exec.return_value = mock_flash_proc
        mock_post.return_value = mock_ollama_resp

        res = await router.analyze_and_patch(
            repo_path=tmp_path,
            persona="bolt",
            target_file="app.py",
            issue_context="Boolean flag correction",
            mode=EngineMode.ANTIGRAVITY_FLASH,
        )

        assert isinstance(res, PatchResult)
        assert res.success is True
        assert "local" in res.engine_used.lower()
        assert res.diff is not None
        assert "return True" in res.diff
        assert res.lines_changed == 2


@pytest.mark.asyncio
async def test_fallback_when_both_flash_and_local_fail(tmp_path: Path):
    """When Flash AND Local both fail, returns PatchResult(success=False) without raising exceptions."""
    target = tmp_path / "app.py"
    target.write_text("import os\n", encoding="utf-8")

    router = EngineRouter(allow_fallback=True)

    # Flash crashes
    mock_flash_proc = MagicMock()
    mock_flash_proc.returncode = 2
    mock_flash_proc.communicate = AsyncMock(return_value=(b"", b"Fatal: CLI unavailable"))

    # Ollama endpoint unreachable
    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:

        mock_exec.return_value = mock_flash_proc
        mock_post.side_effect = httpx.ConnectError("Ollama daemon down")

        res = await router.analyze_and_patch(
            repo_path=tmp_path,
            persona="sentinel",
            target_file="app.py",
            issue_context="Security audit",
            mode=EngineMode.ANTIGRAVITY_FLASH,
        )

        # Invariant: structured failure, no unhandled exception
        assert isinstance(res, PatchResult)
        assert res.success is False
        assert res.error is not None
        assert "Flash failed" in res.error
        assert "Local fallback failed" in res.error


# ---------------------------------------------------------------------------
# Mode: Hybrid
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mode_hybrid_success(tmp_path: Path):
    """Hybrid mode performs local AST heuristic targeting and passes snippet to Flash."""
    target = tmp_path / "calculator.py"
    target.write_text(
        "class Calculator:\n"
        "    def slow_compute(self, n: int) -> int:\n"
        "        # line 3: unoptimized computation\n"
        "        total = 0\n"
        "        for i in range(n):\n"
        "            total += i\n"
        "        return total\n",
        encoding="utf-8",
    )

    diff_output = (
        "--- a/calculator.py\n"
        "+++ b/calculator.py\n"
        "@@ -4,4 +4,2 @@\n"
        "-        total = 0\n"
        "-        for i in range(n):\n"
        "-            total += i\n"
        "-        return total\n"
        "+        return n * (n - 1) // 2\n"
    )

    ndjson = json.dumps({"type": "result", "diff": diff_output}) + "\n"

    router = EngineRouter()

    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.communicate = AsyncMock(return_value=(ndjson.encode("utf-8"), b""))

    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = mock_proc

        res = await router.analyze_and_patch(
            repo_path=tmp_path,
            persona="bolt",
            target_file="calculator.py",
            issue_context="slow_compute loop: replace O(n) loop with mathematical formula",
            mode=EngineMode.HYBRID,
        )

        assert isinstance(res, PatchResult)
        assert res.success is True
        assert res.engine_used == "hybrid"
        assert res.diff is not None
        assert "n * (n - 1) // 2" in res.diff

        # Verify candidate snippet was targeted in prompt
        cmd_args, _ = mock_exec.call_args
        prompt_arg = cmd_args[-1]
        assert "Candidate Code Section" in prompt_arg
        assert "slow_compute" in prompt_arg


@pytest.mark.asyncio
async def test_mode_hybrid_fallback_to_local(tmp_path: Path):
    """When Flash fails in Hybrid mode, degrades to Local Ollama with candidate targeting."""
    target = tmp_path / "math_util.py"
    target.write_text("def square(x):\n    return x * x\n", encoding="utf-8")

    diff_payload = (
        "```diff\n"
        "--- a/math_util.py\n"
        "+++ b/math_util.py\n"
        "@@ -1,2 +1,2 @@\n"
        " def square(x):\n"
        "-    return x * x\n"
        "+    return x ** 2\n"
        "```"
    )

    router = EngineRouter(allow_fallback=True)

    mock_flash_proc = MagicMock()
    mock_flash_proc.returncode = 127
    mock_flash_proc.communicate = AsyncMock(return_value=(b"", b"agy binary not found"))

    mock_ollama_resp = MagicMock(spec=httpx.Response)
    mock_ollama_resp.status_code = 200
    mock_ollama_resp.json.return_value = {"response": diff_payload}
    mock_ollama_resp.raise_for_status = MagicMock()

    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:

        mock_exec.return_value = mock_flash_proc
        mock_post.return_value = mock_ollama_resp

        res = await router.analyze_and_patch(
            repo_path=tmp_path,
            persona="bolt",
            target_file="math_util.py",
            issue_context="Replace x * x with x ** 2",
            mode=EngineMode.HYBRID,
        )

        assert isinstance(res, PatchResult)
        assert res.success is True
        assert "local" in res.engine_used.lower()
        assert res.diff is not None


# ---------------------------------------------------------------------------
# Invariants, Security & Safety Guards
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_path_traversal_guard(tmp_path: Path):
    """Verify paths attempting traversal outside repository root are strictly blocked."""
    router = EngineRouter()
    res = await router.analyze_and_patch(
        repo_path=tmp_path,
        persona="sentinel",
        target_file="../../etc/passwd",
        issue_context="Check sensitive file",
    )
    assert res.success is False
    assert "traversal" in res.error.lower()


@pytest.mark.asyncio
async def test_nonexistent_repo_or_target_file(tmp_path: Path):
    """Verify non-existent repository or target file produces clean PatchResult(success=False)."""
    router = EngineRouter()

    # Non-existent repo
    res_repo = await router.analyze_and_patch(
        repo_path=tmp_path / "nonexistent_dir",
        persona="bolt",
        target_file="some_file.py",
        issue_context="Test non-existent repo",
    )
    assert res_repo.success is False
    assert "does not exist" in res_repo.error

    # Non-existent target file
    res_file = await router.analyze_and_patch(
        repo_path=tmp_path,
        persona="bolt",
        target_file="missing.py",
        issue_context="Test missing file",
    )
    assert res_file.success is False
    assert "does not exist" in res_file.error


@pytest.mark.asyncio
async def test_process_group_kill_on_timeout(tmp_path: Path):
    """Verify subprocess timeout triggers os.killpg to prevent orphan processes."""
    target = tmp_path / "worker.py"
    target.write_text("import time\ntime.sleep(100)\n", encoding="utf-8")

    router = EngineRouter(subprocess_timeout=1.0, allow_fallback=False)

    mock_proc = MagicMock()
    mock_proc.pid = 99999
    # Simulate timeout on communicate
    mock_proc.communicate = AsyncMock(side_effect=asyncio.TimeoutError())

    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec, \
         patch("os.getpgid", return_value=99999) as mock_getpgid, \
         patch("os.killpg") as mock_killpg:

        mock_exec.return_value = mock_proc

        res = await router.analyze_and_patch(
            repo_path=tmp_path,
            persona="bolt",
            target_file="worker.py",
            issue_context="Long running task",
            mode=EngineMode.ANTIGRAVITY_FLASH,
        )

        assert res.success is False
        assert "timed out" in res.error.lower()
        mock_getpgid.assert_called_with(99999)
        mock_killpg.assert_called_with(99999, signal.SIGKILL)


@pytest.mark.asyncio
async def test_scope_ceiling_enforcement(tmp_path: Path):
    """Verify scope ceiling enforcement flags patches exceeding max_lines."""
    target = tmp_path / "big_change.py"
    target.write_text("line\n" * 100, encoding="utf-8")

    # Generate diff of 60 lines
    diff_lines = ["--- a/big_change.py\n+++ b/big_change.py\n@@ -1,30 +1,60 @@\n"]
    for i in range(30):
        diff_lines.append(f"-old {i}\n")
    for i in range(30):
        diff_lines.append(f"+new {i}\n")
    big_diff = "".join(diff_lines)

    router = EngineRouter(max_lines=50, enforce_scope_ceiling=True)

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"response": f"```diff\n{big_diff}```"}
    mock_resp.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        res = await router.analyze_and_patch(
            repo_path=tmp_path,
            persona="bolt",
            target_file="big_change.py",
            issue_context="Exceeds 50 lines",
            mode=EngineMode.LOCAL,
        )

        assert res.success is False
        assert res.lines_changed == 60
        assert "scope ceiling" in res.error.lower()


def test_personas_registry_available():
    """Verify Bolt, Palette, and Sentinel personas are configured in models."""
    assert "bolt" in PERSONAS
    assert "palette" in PERSONAS
    assert "sentinel" in PERSONAS
    assert PERSONAS["bolt"]["icon"] == "⚡"
    assert PERSONAS["palette"]["icon"] == "🎨"
    assert PERSONAS["sentinel"]["icon"] == "🛡️"
