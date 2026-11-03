"""
Julius Hub Scanner: Repository inspection and issue suggestion engine.
Extracts micro-improvements across Bolt (Performance), Palette (UX/Hygiene),
and Sentinel (Security) personas, as well as CI failure tracebacks.

All subprocess executions use typed argument lists (list[str]) with shell=False.
"""

import json
import logging
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Collection, Dict, List, Optional, Set, Union

from hub.models import Suggestion

logger = logging.getLogger("hub.scanner")


def run_cmd(
    cmd: List[str],
    cwd: Optional[Union[str, Path]] = None,
    check: bool = True,
    input_str: Optional[str] = None,
    timeout: Optional[float] = None,
) -> subprocess.CompletedProcess:
    """
    Run a subprocess command safely without shell redirection.
    Enforces typed list[str] arguments and shell=False.
    """
    if not isinstance(cmd, list) or not all(isinstance(arg, str) for arg in cmd):
        raise TypeError(f"Command must be a list of strings, got: {type(cmd)}")

    resolved_cwd = str(cwd) if cwd is not None else None
    result = subprocess.run(
        cmd,
        cwd=resolved_cwd,
        input=input_str,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        shell=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(cmd)}\n"
            f"Stdout: {result.stdout.strip()}\n"
            f"Stderr: {result.stderr.strip()}"
        )
    return result


def find_suggestions(
    repo_path: Union[str, Path],
    mode: str = "all",
    category: str = "all",
    ignored_ids: Optional[Union[Set[str], List[str], Collection[str]]] = None,
) -> List[Suggestion]:
    """
    Scan repository for concrete micro-improvements across Bolt, Palette, or Sentinel.
    Filters out any suggestions matching ignored_ids.
    Returns a typed list of Suggestion models.
    """
    repo = Path(repo_path).resolve()
    if not repo.exists():
        raise FileNotFoundError(f"Repository path does not exist: {repo}")

    raw_suggestions: List[Dict[str, Any]] = []
    mode_clean = mode.lower()
    modes_to_scan = ["bolt", "palette", "sentinel"] if mode_clean == "all" else [mode_clean]

    ignore_dirs = {
        ".git", ".venv", "node_modules", "worktrees", ".worktrees", "__pycache__",
        "dist", "build", ".next", "coverage", ".turbo", ".cache", ".pytest_cache",
        ".stfolder", "data", "fixtures", "graphify-out"
    }

    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith(".st")]
        for file in files:
            file_path = Path(root) / file
            try:
                rel_path = file_path.relative_to(repo)
            except ValueError:
                rel_path = file_path

            # Sentinel checks (Security)
            if "sentinel" in modes_to_scan and file.endswith((".py", ".ts", ".js", ".json")):
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                    for idx, line in enumerate(lines, 1):
                        if "shell=True" in line and "subprocess" in line:
                            raw_suggestions.append({
                                "id": f"sentinel-{len(raw_suggestions)+1}",
                                "persona": "sentinel",
                                "category": "security",
                                "title": "Avoid shell=True in subprocess calls",
                                "file": str(rel_path),
                                "line": idx,
                                "issue": "Passing shell=True introduces command injection risks if inputs are unsanitized.",
                                "impact": "Neutralizes shell injection vectors.",
                                "code_snippet": line.strip(),
                            })
                        if any(k in line.lower() for k in ["secret_key =", "jwt_secret =", "default_password ="]) and any(
                            w in line for w in ["'secret'", '"secret"', "'password'", '"password"', "'admin'"]
                        ):
                            raw_suggestions.append({
                                "id": f"sentinel-{len(raw_suggestions)+1}",
                                "persona": "sentinel",
                                "category": "security",
                                "title": "Hardcoded default credential or secret fallback",
                                "file": str(rel_path),
                                "line": idx,
                                "issue": "Hardcoded fallback credentials can be used as insecure defaults in production.",
                                "impact": "Enforces explicit secure environment configuration.",
                                "code_snippet": line.strip(),
                            })
                        # SQL Injection in DDL
                        if any(stmt in line for stmt in ["CREATE DATABASE", "DROP DATABASE", "ALTER TABLE"]) and any(
                            c in line for c in ['f"', "f'", ".format(", "%s"]
                        ):
                            ddl_op = (
                                "CREATE DATABASE"
                                if "CREATE DATABASE" in line
                                else ("DROP DATABASE" if "DROP DATABASE" in line else "ALTER TABLE")
                            )
                            raw_suggestions.append({
                                "id": f"sentinel-{len(raw_suggestions)+1}",
                                "persona": "sentinel",
                                "category": "security",
                                "title": f"SQL Injection in {ddl_op}",
                                "file": str(rel_path),
                                "line": idx,
                                "issue": f"Dynamic string formatting in {ddl_op} bypasses parameterized queries.",
                                "impact": "Validate identifier with strict regex ^[a-zA-Z0-9_]+$ or quote securely.",
                                "code_snippet": line.strip(),
                            })
                        # Overly permissive CORS
                        if "allow_origin_regex" in line and any(c in line for c in [r"\d{1,3}", "localhost"]):
                            raw_suggestions.append({
                                "id": f"sentinel-{len(raw_suggestions)+1}",
                                "persona": "sentinel",
                                "category": "security",
                                "title": "Overly Permissive CORS Regex",
                                "file": str(rel_path),
                                "line": idx,
                                "issue": "Matching broad local/private IP regex patterns in CORS can allow unauthorized cross-origin requests.",
                                "impact": "Restrict CORS explicitly to trusted origins.",
                                "code_snippet": line.strip(),
                            })
                        # Empty except block
                        if line.strip().startswith("except Exception:") or line.strip() == "except:":
                            if idx < len(lines) and lines[idx].strip() in ["pass", "continue"]:
                                raw_suggestions.append({
                                    "id": f"sentinel-{len(raw_suggestions)+1}",
                                    "persona": "sentinel",
                                    "category": "security",
                                    "title": "Remove empty except Exception block",
                                    "file": str(rel_path),
                                    "line": idx,
                                    "issue": "Silently suppressing exceptions with pass hides underlying bugs and operational errors.",
                                    "impact": "Add logger warning or handle specific exception types.",
                                    "code_snippet": f"{line.strip()} {lines[idx].strip()}",
                                })
                except Exception as e:
                    logger.debug("Error scanning sentinel rules on %s: %s", file_path, e)

            # Palette checks (UX & Code Hygiene)
            if "palette" in modes_to_scan and file.endswith((".tsx", ".jsx", ".html", ".py")):
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                    for idx, line in enumerate(lines, 1):
                        if "<button" in line and not any(a in line for a in ["aria-label", "aria-labelledby"]):
                            sub_block = "".join(lines[idx - 1 : min(len(lines), idx + 3)])
                            if any(ic in sub_block for ic in ["Icon", "Svg", "svg", "Trash", "Close", "Edit", "Plus", "Delete"]):
                                raw_suggestions.append({
                                    "id": f"palette-{len(raw_suggestions)+1}",
                                    "persona": "palette",
                                    "category": "cleanup",
                                    "title": "Icon-only button missing aria-label",
                                    "file": str(rel_path),
                                    "line": idx,
                                    "issue": "Screen readers cannot announce the purpose of buttons containing only icons.",
                                    "impact": "Improves WCAG compliance and accessibility for assistive technology.",
                                    "code_snippet": line.strip(),
                                })
                        if line.strip() == "pass" and idx > 1:
                            prev = lines[idx - 2].strip()
                            if any(prev.endswith(k) for k in [":", "return", "pass"]) or prev.startswith("return"):
                                raw_suggestions.append({
                                    "id": f"palette-{len(raw_suggestions)+1}",
                                    "persona": "palette",
                                    "category": "code_health",
                                    "title": f"Remove empty pass block in {file_path.stem}",
                                    "file": str(rel_path),
                                    "line": idx,
                                    "issue": "Redundant pass statement can be removed for cleaner code.",
                                    "impact": "Improves code hygiene and readability.",
                                    "code_snippet": f"{prev} -> pass",
                                })
                except Exception as e:
                    logger.debug("Error scanning palette rules on %s: %s", file_path, e)

            # Bolt checks (Performance)
            if "bolt" in modes_to_scan and file.endswith((".py", ".ts", ".js")):
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                    for idx, line in enumerate(lines, 1):
                        if "strptime(" in line and any("for " in lines[max(0, idx - 4) : idx][i] for i in range(len(lines[max(0, idx - 4) : idx]))):
                            raw_suggestions.append({
                                "id": f"bolt-{len(raw_suggestions)+1}",
                                "persona": "bolt",
                                "category": "performance",
                                "title": "Repeated datetime.strptime inside loop",
                                "file": str(rel_path),
                                "line": idx,
                                "issue": "datetime.strptime introduces heavy parsing overhead when called repeatedly inside loops.",
                                "impact": "Pre-computing or replacing with fromisoformat yields a 4x-5x speedup.",
                                "code_snippet": line.strip(),
                            })
                        # N+1 queries in loops
                        if "for " in line and any(k in line for k in [" in ", ":"]):
                            loop_block = "".join(lines[idx : min(len(lines), idx + 6)])
                            if any(q in loop_block for q in ["db.query(", "session.query("]) and any(
                                op in loop_block for op in [".delete(", ".all()", ".first()"]
                            ):
                                if not any(b in loop_block for b in ["bulk_", ".in_("]):
                                    raw_suggestions.append({
                                        "id": f"bolt-{len(raw_suggestions)+1}",
                                        "persona": "bolt",
                                        "category": "performance",
                                        "title": f"N+1 Query in {file_path.stem}",
                                        "file": str(rel_path),
                                        "line": idx,
                                        "issue": "Database query executed inside iteration loop causes repeated network/DB roundtrips.",
                                        "impact": "Consolidate into a single bulk query with in_() for 10x-100x speedup.",
                                        "code_snippet": line.strip(),
                                    })
                        # Suboptimal loop finding item in list
                        if "for " in line and any(k in line for k in [" in ", ":"]):
                            loop_block = "".join(lines[idx : min(len(lines), idx + 3)])
                            if "if " in loop_block and any(op in loop_block for op in ["==", "is "]) and "return " in loop_block:
                                raw_suggestions.append({
                                    "id": f"bolt-{len(raw_suggestions)+1}",
                                    "persona": "bolt",
                                    "category": "performance",
                                    "title": "Suboptimal Loop Finding Item in List",
                                    "file": str(rel_path),
                                    "line": idx,
                                    "issue": "Iterating linearly over a collection to return a single match can be replaced with next() or dictionary lookup.",
                                    "impact": "Reduces O(n) scan to O(1) dictionary retrieval or concise generator.",
                                    "code_snippet": line.strip(),
                                })
                except Exception as e:
                    logger.debug("Error scanning bolt rules on %s: %s", file_path, e)

    # Test Gap Scanner (Palette / Craftsman)
    if any(m in modes_to_scan for m in ["palette", "bolt", "sentinel"]):
        tests_dir = repo / "tests"
        if tests_dir.exists():
            test_stems = {f.stem.replace("test_", "") for f in tests_dir.rglob("test_*.py")}
            for check_dir_name in ["src", "apps/api/routers", "apps/api/services"]:
                target_check_dir = repo / check_dir_name
                if target_check_dir.exists():
                    for src_file in target_check_dir.rglob("*.py"):
                        if src_file.name.startswith("__"):
                            continue
                        stem = src_file.stem
                        if stem not in test_stems and f"test_{stem}" not in test_stems:
                            try:
                                rel_src = src_file.relative_to(repo)
                            except ValueError:
                                rel_src = src_file
                            raw_suggestions.append({
                                "id": f"craftsman-{len(raw_suggestions)+1}",
                                "persona": "palette",
                                "category": "testing",
                                "title": f"Missing test file for {src_file.name}",
                                "file": str(rel_src),
                                "line": 1,
                                "issue": f"Module {src_file.name} lacks a dedicated unit test suite in tests/.",
                                "impact": "Ensures regression safety and automated test coverage.",
                                "code_snippet": f"tests/test_{stem}.py",
                            })

    if category != "all":
        cat_clean = category.lower()
        category_aliases = {
            "hygiene": {"cleanup", "code_health", "hygiene"},
            "cleanup": {"cleanup", "hygiene"},
            "code_health": {"code_health", "hygiene"},
            "tests": {"testing", "tests"},
            "testing": {"testing", "tests"},
            "security": {"security"},
            "performance": {"performance"},
        }
        allowed = category_aliases.get(cat_clean, {cat_clean})
        raw_suggestions = [s for s in raw_suggestions if s.get("category") in allowed]

    ignored = set(ignored_ids) if ignored_ids else set()
    suggestions = [Suggestion(**s) for s in raw_suggestions]
    if ignored:
        suggestions = [s for s in suggestions if s.id not in ignored]

    return suggestions


def get_failing_pr(
    repo_path: Union[str, Path],
    pr_number: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """
    Fetch PR details and checks status using GitHub CLI ('gh').
    Uses list[str] subprocess execution with shell=False.
    """
    repo = Path(repo_path).resolve()
    if not shutil.which("gh"):
        logger.warning("GitHub CLI ('gh') is not installed or not in PATH.")
        return None

    try:
        if pr_number is not None:
            cmd = ["gh", "pr", "view", str(pr_number), "--json", "number,headRefName,title,state,url"]
            res = run_cmd(cmd, cwd=repo, check=True)
            pr_data = json.loads(res.stdout)
        else:
            cmd = ["gh", "pr", "list", "--state", "open", "--limit", "5", "--json", "number,headRefName,title,state,url"]
            res = run_cmd(cmd, cwd=repo, check=True)
            prs = json.loads(res.stdout) if res.stdout.strip() else []
            if not prs:
                logger.info("No open pull requests found for repository: %s", repo)
                return None
            pr_data = prs[0]

        checks_cmd = ["gh", "pr", "checks", str(pr_data["number"]), "--json", "name,state,bucket,event"]
        checks_res = run_cmd(checks_cmd, cwd=repo, check=False)
        checks = json.loads(checks_res.stdout) if checks_res.returncode == 0 and checks_res.stdout.strip() else []
        failing_checks = [
            c for c in checks
            if c.get("bucket") in ["fail", "error"] or c.get("state") in ["FAILURE", "ERROR"]
        ]

        pr_data["checks"] = checks
        pr_data["failing_checks"] = failing_checks
        return pr_data
    except Exception as e:
        logger.error("Failed to query GitHub PR: %s", e)
        return None


def fetch_ci_failure_log(
    repo_path: Union[str, Path],
    branch: str,
) -> str:
    """
    Fetch failing CI logs for a branch via GitHub CLI ('gh').
    Condenses error trace via local LLM if script exists and log exceeds 20KB.
    Uses list[str] subprocess execution with shell=False.
    """
    repo = Path(repo_path).resolve()
    if not shutil.which("gh"):
        return ""

    try:
        cmd_runs = ["gh", "run", "list", "--branch", branch, "--limit", "1", "--json", "databaseId,conclusion"]
        res = run_cmd(cmd_runs, cwd=repo, check=False)
        runs = json.loads(res.stdout) if res.returncode == 0 and res.stdout.strip() else []
        if not runs or runs[0].get("conclusion") != "failure":
            return ""

        run_id = runs[0]["databaseId"]
        cmd_view = ["gh", "run", "view", str(run_id), "--log-failed"]
        log_res = run_cmd(cmd_view, cwd=repo, check=False)
        raw_log = log_res.stdout.strip()

        if len(raw_log) > 20000:
            offload_script_env = os.getenv("LOCAL_LLM_OFFLOAD_SCRIPT", "")
            if offload_script_env and Path(offload_script_env).exists():
                offload_script = Path(offload_script_env)
                condense_cmd = [
                    sys.executable,
                    str(offload_script),
                    "--task",
                    "log-extract",
                    "--prompt",
                    "Extract exact error, failing tests, and file locations",
                ]
                condense_res = run_cmd(condense_cmd, input_str=raw_log, cwd=repo, check=False)
                if condense_res.returncode == 0 and condense_res.stdout.strip():
                    return condense_res.stdout.strip()

        return raw_log[:8000]
    except Exception as e:
        logger.warning("Error fetching CI failure logs for branch '%s': %s", branch, e)
        return ""
