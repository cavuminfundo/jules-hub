"""
Unit tests for Jules Hub Scanner (hub/scanner.py).
Verifies detection of micro-improvements across Bolt (Performance),
Palette (UX/Hygiene/Tests), and Sentinel (Security) personas, as well as
filtering and GitHub CI log handling.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from hub.models import Suggestion
from hub.scanner import (
    find_suggestions,
    get_failing_pr,
    fetch_ci_failure_log,
)


def test_sentinel_suggestions(tmp_path: Path):
    """Verify Sentinel detects security vulnerabilities."""
    sample_file = tmp_path / "security_sample.py"
    sample_file.write_text(
        "import subprocess\n"
        "subprocess.run('ls -la', shell=True)\n"
        "secret_key = 'secret'\n"
        "def query_db(name):\n"
        "    sql = f'CREATE DATABASE {name}'\n"
        "allow_origin_regex = r'http://192.168.1.\\d{1,3}'\n"
        "try:\n"
        "    dangerous_call()\n"
        "except Exception:\n"
        "    pass\n",
        encoding="utf-8",
    )

    suggestions = find_suggestions(tmp_path, mode="sentinel", category="all")
    assert len(suggestions) >= 4

    titles = [s.title for s in suggestions]
    assert any("shell=True" in t for t in titles)
    assert any("Hardcoded default credential" in t for t in titles)
    assert any("SQL Injection in CREATE DATABASE" in t for t in titles)
    assert any("Overly Permissive CORS Regex" in t for t in titles)
    assert any("Remove empty except Exception block" in t for t in titles)

    for s in suggestions:
        assert isinstance(s, Suggestion)
        assert s.persona == "sentinel"
        assert s.category == "security"
        # Test backward-compatible dict access
        assert s.get("category") == "security"
        assert s["persona"] == "sentinel"


def test_palette_suggestions(tmp_path: Path):
    """Verify Palette detects UX, hygiene, and test coverage gaps."""
    # 1. Accessibility gap in React/JSX
    ui_file = tmp_path / "Widget.tsx"
    ui_file.write_text(
        "export const Widget = () => (\n"
        "  <button className='p-2'>\n"
        "    <TrashIcon />\n"
        "  </button>\n"
        ");\n",
        encoding="utf-8",
    )

    # 2. Hygiene pass block
    py_file = tmp_path / "clean.py"
    py_file.write_text(
        "def helper():\n"
        "    return 1\n"
        "    pass\n",
        encoding="utf-8",
    )

    # 3. Test gap
    src_dir = tmp_path / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "payment_gateway.py").write_text("def process(): return True\n", encoding="utf-8")

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "test_other.py").write_text("def test_ok(): pass\n", encoding="utf-8")

    suggestions = find_suggestions(tmp_path, mode="palette", category="all")
    titles = [s.title for s in suggestions]

    assert any("Icon-only button missing aria-label" in t for t in titles)
    assert any("Remove empty pass block" in t for t in titles)
    assert any("Missing test file for payment_gateway.py" in t for t in titles)

    for s in suggestions:
        assert s.persona == "palette"
        assert s.category in {"hygiene", "tests"}


def test_bolt_suggestions(tmp_path: Path):
    """Verify Bolt detects performance bottlenecks."""
    perf_file = tmp_path / "optimizations.py"
    perf_file.write_text(
        "import datetime\n"
        "for raw_str in date_list:\n"
        "    dt = datetime.strptime(raw_str, '%Y-%m-%d')\n"
        "\n"
        "for user_id in user_ids:\n"
        "    record = session.query(User).filter_by(id=user_id).first()\n"
        "\n"
        "for item in big_list:\n"
        "    if item.id == target_id:\n"
        "        return item\n",
        encoding="utf-8",
    )

    suggestions = find_suggestions(tmp_path, mode="bolt", category="all")
    assert len(suggestions) >= 3

    titles = [s.title for s in suggestions]
    assert any("Repeated datetime.strptime inside loop" in t for t in titles)
    assert any("N+1 Query" in t for t in titles)
    assert any("Suboptimal Loop Finding Item in List" in t for t in titles)

    for s in suggestions:
        assert s.persona == "bolt"
        assert s.category == "performance"


def test_mode_and_category_filtering(tmp_path: Path):
    """Verify mode and category filters correctly partition results."""
    # Create mixed issues
    sec_file = tmp_path / "sec.py"
    sec_file.write_text("import subprocess\nsubprocess.run(['ls'], shell=True)\n", encoding="utf-8")

    perf_file = tmp_path / "perf.py"
    perf_file.write_text("for d in dates:\n    datetime.strptime(d, '%Y-%m-%d')\n", encoding="utf-8")

    # Mode filter: sentinel only
    sentinel_only = find_suggestions(tmp_path, mode="sentinel", category="all")
    assert all(s.persona == "sentinel" for s in sentinel_only)
    assert any(s.category == "security" for s in sentinel_only)

    # Category filter: performance only
    perf_only = find_suggestions(tmp_path, mode="all", category="performance")
    assert all(s.category == "performance" for s in perf_only)

    # All mode and category
    all_results = find_suggestions(tmp_path, mode="all", category="all")
    categories_found = {s.category for s in all_results}
    assert "security" in categories_found
    assert "performance" in categories_found


@patch("hub.scanner.shutil.which")
@patch("hub.scanner.run_cmd")
def test_get_failing_pr(mock_run_cmd, mock_which, tmp_path: Path):
    """Verify get_failing_pr handles gh checks and failing checks correctly."""
    mock_which.return_value = "/usr/bin/gh"

    pr_view_stdout = json.dumps({
        "number": 42,
        "headRefName": "fix/memory-leak",
        "title": "Fix memory leak",
        "state": "OPEN",
        "url": "https://github.com/test/repo/pull/42",
    })

    checks_stdout = json.dumps([
        {"name": "pytest", "state": "FAILURE", "bucket": "fail"},
        {"name": "lint", "state": "SUCCESS", "bucket": "pass"},
    ])

    mock_run_cmd.side_effect = [
        MagicMock(stdout=pr_view_stdout, returncode=0),
        MagicMock(stdout=checks_stdout, returncode=0),
    ]

    pr_data = get_failing_pr(tmp_path, pr_number=42)
    assert pr_data is not None
    assert pr_data["number"] == 42
    assert pr_data["headRefName"] == "fix/memory-leak"
    assert len(pr_data["failing_checks"]) == 1
    assert pr_data["failing_checks"][0]["name"] == "pytest"


@patch("hub.scanner.shutil.which")
def test_get_failing_pr_no_gh(mock_which, tmp_path: Path):
    """Verify get_failing_pr returns None gracefully when gh is not installed."""
    mock_which.return_value = None
    pr_data = get_failing_pr(tmp_path)
    assert pr_data is None


@patch("hub.scanner.shutil.which")
@patch("hub.scanner.run_cmd")
def test_fetch_ci_failure_log(mock_run_cmd, mock_which, tmp_path: Path):
    """Verify fetch_ci_failure_log retrieves failing run logs."""
    mock_which.return_value = "/usr/bin/gh"

    runs_stdout = json.dumps([{"databaseId": 123456, "conclusion": "failure"}])
    log_stdout = "FAILED tests/test_core.py::test_eval - AssertionError\n"

    mock_run_cmd.side_effect = [
        MagicMock(stdout=runs_stdout, returncode=0),
        MagicMock(stdout=log_stdout, returncode=0),
    ]

    log = fetch_ci_failure_log(tmp_path, branch="main")
    assert "AssertionError" in log
