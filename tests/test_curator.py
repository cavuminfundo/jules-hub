"""
Unit tests for Jules Curator Hub (curator.py)
Validating suggest category filter and limit options.
"""

import sys
import tempfile
from pathlib import Path

# Add repo root to sys.path so curator can be imported
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from curator import build_parser, find_suggestions

try:
    import pytest
except ImportError:
    pytest = None


def test_suggest_parser_arguments():
    """
    Verifica che l'argparser del comando 'suggest' accetti:
    - --category, -c con choices=["all", "security", "performance", "hygiene", "tests"] e default="all"
    - --limit, -l con type=int e default=None
    """
    parser = build_parser()

    # Default values
    args_default = parser.parse_args(["suggest", "--repo", "demo_repo"])
    assert args_default.category == "all"
    assert args_default.limit is None

    # Valid choices for --category
    valid_categories = ["all", "security", "performance", "hygiene", "tests"]
    for cat in valid_categories:
        args = parser.parse_args(["suggest", "--repo", "demo_repo", "--category", cat, "--limit", "10"])
        assert args.category == cat
        assert args.limit == 10

    # Short options -c and -l
    args_short = parser.parse_args(["suggest", "-r", "demo_repo", "-c", "security", "-l", "3"])
    assert args_short.category == "security"
    assert args_short.limit == 3

    # Invalid category choice must raise SystemExit
    if pytest is not None:
        with pytest.raises(SystemExit):
            parser.parse_args(["suggest", "--repo", "demo_repo", "--category", "invalid_choice"])
    else:
        try:
            parser.parse_args(["suggest", "--repo", "demo_repo", "--category", "invalid_choice"])
            assert False, "Expected SystemExit for invalid category"
        except SystemExit:
            pass

    # Non-integer limit must raise SystemExit
    if pytest is not None:
        with pytest.raises(SystemExit):
            parser.parse_args(["suggest", "--repo", "demo_repo", "--limit", "not_a_number"])
    else:
        try:
            parser.parse_args(["suggest", "--repo", "demo_repo", "--limit", "not_a_number"])
            assert False, "Expected SystemExit for non-integer limit"
        except SystemExit:
            pass


def _run_category_filter_checks(root_path: Path):
    """Core assertion logic for find_suggestions category filter and tags."""
    # 1. Populate sample files covering each category

    # Sentinel: Security
    sec_file = root_path / "sentinel_sample.py"
    sec_file.write_text(
        "import subprocess\n"
        "subprocess.run('ls -la', shell=True)\n",
        encoding="utf-8",
    )

    # Bolt: Performance
    perf_file = root_path / "bolt_sample.py"
    perf_file.write_text(
        "import datetime\n"
        "for d in raw_dates:\n"
        "    datetime.strptime(d, '%Y-%m-%d')\n",
        encoding="utf-8",
    )

    # Palette: Hygiene
    hygiene_file = root_path / "palette_sample.tsx"
    hygiene_file.write_text(
        "export const Component = () => (\n"
        "  <button className=\"btn\">\n"
        "    <Trash />\n"
        "  </button>\n"
        ");\n",
        encoding="utf-8",
    )

    # Craftsman: Tests
    src_dir = root_path / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "worker.py").write_text("def do_work():\n    return 42\n", encoding="utf-8")

    tests_dir = root_path / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "test_unrelated.py").write_text("def test_ok(): assert True\n", encoding="utf-8")

    # 2. Test category="all": all 4 categories must be present
    all_suggestions = find_suggestions(root_path, mode="all", category="all")
    found_categories = {s.get("category") for s in all_suggestions}

    assert "security" in found_categories, f"Missing 'security' category in {found_categories}"
    assert "performance" in found_categories, f"Missing 'performance' category in {found_categories}"
    assert "hygiene" in found_categories, f"Missing 'hygiene' category in {found_categories}"
    assert "tests" in found_categories, f"Missing 'tests' category in {found_categories}"

    for s in all_suggestions:
        assert s.get("category") in {"security", "performance", "hygiene", "tests"}

    # 3. Test filtering per specific category
    for cat in ["security", "performance", "hygiene", "tests"]:
        filtered = find_suggestions(root_path, mode="all", category=cat)
        assert len(filtered) > 0, f"Expected at least one suggestion for category '{cat}'"
        assert all(s.get("category") == cat for s in filtered), (
            f"Filtered results for category '{cat}' contained unexpected categories: "
            f"{[s.get('category') for s in filtered]}"
        )


def test_find_suggestions_category_filter(tmp_path=None):
    """
    Verifica con dati temporanei che find_suggestions assegni correttamente il campo 'category'
    a ciascuna suggestione ('security', 'performance', 'hygiene', 'tests') e filtri per category.
    """
    if tmp_path is not None:
        _run_category_filter_checks(Path(tmp_path))
    else:
        with tempfile.TemporaryDirectory() as td:
            _run_category_filter_checks(Path(td))


if __name__ == "__main__":
    test_suggest_parser_arguments()
    test_find_suggestions_category_filter()
    print("All unit tests passed successfully!")
