#!/usr/bin/env python3
"""
Jules Curator Hub — Autonomous Background Worktree Runner
=========================================================
Runs hyper-specialized micro-improvement personas (Bolt ⚡, Palette 🎨, Sentinel 🛡️)
inside 100% isolated git worktrees, protecting the developer's primary working tree
from any interference, unstaged changes, or branch switches.

Principles inherited from Jules:
- Scope ceiling: ONE atomic improvement < 50 lines.
- Zero-noise fallback: If no clear win is identified, stop and do not modify.
- Isolated execution: All changes, tests, and commits happen in worktrees/
- Critical learnings only: Journal only unexpected traps or architectural insights.
"""

import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

HUB_DIR = Path("/home/federico/jules")
WORKTREES_DIR = HUB_DIR / "worktrees"
JOURNAL_DIR = HUB_DIR / "journal"
PROJECTS_REGISTRY = Path("/home/federico/.gemini/config/projects_registry.json")

PERSONAS = {
    "bolt": {
        "name": "Bolt ⚡",
        "role": "Performance-Obsessed Optimizer",
        "mission": "Identify and implement ONE small performance improvement (< 50 lines) that makes the application measurably faster or more efficient.",
        "icon": "⚡",
        "focus": [
            "N+1 query problems in database/ORM calls",
            "Missing indexes or unoptimized lookups (O(n²) to O(n))",
            "Unnecessary re-renders or missing memoization (React.memo, useMemo)",
            "Synchronous operations blocking async loops",
            "Missing debouncing/throttling on frequent events",
            "Redundant calculations in loops or missing early returns",
            "Missing pagination on large datasets",
        ],
        "avoids": [
            "Micro-optimizations with no measurable impact",
            "Premature optimization of cold paths",
            "Sacrificing code readability",
            "Large architectural changes",
        ],
        "pr_prefix": "⚡ Bolt: [performance improvement]",
    },
    "palette": {
        "name": "Palette 🎨",
        "role": "UX & Accessibility Craftsperson",
        "mission": "Find and implement ONE micro-UX/a11y improvement (< 50 lines) that makes the interface more intuitive, accessible, or pleasant to use.",
        "icon": "🎨",
        "focus": [
            "Missing ARIA labels on icon-only buttons",
            "Missing keyboard navigation support (focus-visible, tab order)",
            "Missing loading spinners/states on async actions",
            "Missing empty states with helpful call-to-actions",
            "Missing disabled states with clear explanation",
            "Form inputs without proper labels or inline error feedback",
            "Insufficient color contrast for better readability",
        ],
        "avoids": [
            "Large design system overhauls",
            "Complete page redesigns",
            "Adding new UI component dependencies",
            "Backend logic changes",
        ],
        "pr_prefix": "🎨 Palette: [UX improvement]",
    },
    "sentinel": {
        "name": "Sentinel 🛡️",
        "role": "Security & Defense Guardian",
        "mission": "Identify and fix ONE small security issue or add ONE defense-in-depth enhancement (< 50 lines) that makes the application more secure.",
        "icon": "🛡️",
        "focus": [
            "Hardcoded secrets, API keys, or tokens in source",
            "SQL injection or command injection risks",
            "Path traversal vulnerabilities (unsanitized input in file paths)",
            "Exposed sensitive data in error messages or logs",
            "Missing authentication/authorization guards on sensitive endpoints",
            "Missing rate limiting or input length limits (DoS prevention)",
            "Missing security headers or overly permissive CORS",
        ],
        "avoids": [
            "Fixing low-priority issues before critical ones",
            "Large security refactors without plan",
            "Changes that break core functionality",
            "Exposing vulnerability details in public commits",
        ],
        "pr_prefix": "🛡️ Sentinel: [security improvement]",
    },
}


def load_knowledge(repo_path: Path, mode: str) -> List[Dict[str, str]]:
    """
    Load accumulated domain knowledge from the repository's .jules/<mode>.md,
    the repo's .agents/memory/lessons.md, and the central Jules journal.
    """
    entries = []
    sources_checked = [
        repo_path / ".jules" / f"{mode}.md",
        repo_path / ".agents" / "memory" / "lessons.md",
        JOURNAL_DIR / f"{mode}.md",
    ]

    for src in sources_checked:
        if not src.exists():
            continue
        try:
            with open(src, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse markdown entries (format: ## YYYY-MM-DD - [Title] ...)
            current_entry: Dict[str, str] = {}
            for line in content.splitlines():
                if line.startswith("## "):
                    if current_entry and current_entry.get("title"):
                        entries.append(current_entry)
                    current_entry = {
                        "source": str(src.relative_to(repo_path) if src.is_relative_to(repo_path) else src.name),
                        "header": line.replace("## ", "").strip(),
                        "body": [],
                    }
                elif current_entry and "body" in current_entry:
                    current_entry["body"].append(line)

            if current_entry and current_entry.get("header"):
                entries.append(current_entry)
        except Exception as e:
            print(f"[WARN] Error reading knowledge from {src}: {e}", file=sys.stderr)

    # Clean body
    for e in entries:
        if isinstance(e.get("body"), list):
            e["text"] = "\n".join(e["body"]).strip()
            del e["body"]

    return entries


def record_learning(
    repo_path: Path,
    mode: str,
    title: str,
    learning: str,
    action: str,
) -> None:
    """
    Record a new critical learning into both the repo's .jules/<mode>.md
    and the central Jules Hub journal.
    """
    today_str = datetime.date.today().isoformat()
    repo_jules_dir = repo_path / ".jules"
    repo_jules_dir.mkdir(parents=True, exist_ok=True)
    repo_journal = repo_jules_dir / f"{mode}.md"
    hub_journal = JOURNAL_DIR / f"{mode}.md"
    JOURNAL_DIR.mkdir(parents=True, exist_ok=True)

    if mode == "sentinel":
        entry_text = f"\n## {today_str} - {title}\n**Vulnerability:** {learning}\n**Learning:** {action}\n**Prevention:** {action}\n"
    else:
        entry_text = f"\n## {today_str} - {title}\n**Learning:** {learning}\n**Action:** {action}\n"

    for dest in [repo_journal, hub_journal]:
        if not dest.exists():
            persona = PERSONAS.get(mode, {"name": mode.capitalize()})
            dest.write_text(f"# {persona['name']} Journal — Critical Learnings Only\n\n---\n", encoding="utf-8")
        with open(dest, "a", encoding="utf-8") as f:
            f.write(entry_text)
        print(f"[KNOWLEDGE] Appended learning to {dest}")


def run_cmd(
    cmd: List[str], cwd: Optional[Path] = None, check: bool = True, input_str: Optional[str] = None
) -> subprocess.CompletedProcess:
    """Run a shell command safely without shell redirection."""
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        input=input_str,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(cmd)}\n"
            f"Stdout: {result.stdout.strip()}\n"
            f"Stderr: {result.stderr.strip()}"
        )
    return result


def get_failing_pr(repo_path: Path, pr_number: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Fetch PR details and checks status using GitHub CLI."""
    if not shutil.which("gh"):
        print("[WARN] GitHub CLI ('gh') is not installed or not in PATH.", file=sys.stderr)
        return None

    try:
        if pr_number:
            res = run_cmd(["gh", "pr", "view", str(pr_number), "--json", "number,headRefName,title,state,url"], cwd=repo_path)
            pr_data = json.loads(res.stdout)
        else:
            # Find open PRs
            res = run_cmd(["gh", "pr", "list", "--state", "open", "--limit", "5", "--json", "number,headRefName,title,state,url"], cwd=repo_path)
            prs = json.loads(res.stdout) if res.stdout.strip() else []
            if not prs:
                print("[INFO] No open pull requests found for this repository.")
                return None
            pr_data = prs[0]

        # Check CI checks
        checks_res = run_cmd(["gh", "pr", "checks", str(pr_data["number"]), "--json", "name,state,bucket,event"], cwd=repo_path, check=False)
        checks = json.loads(checks_res.stdout) if checks_res.returncode == 0 and checks_res.stdout.strip() else []
        failing_checks = [c for c in checks if c.get("bucket") in ["fail", "error"] or c.get("state") in ["FAILURE", "ERROR"]]

        pr_data["checks"] = checks
        pr_data["failing_checks"] = failing_checks
        return pr_data
    except Exception as e:
        print(f"[ERROR] Failed to query GitHub PR: {e}", file=sys.stderr)
        return None


def fetch_ci_failure_log(repo_path: Path, branch_name: str) -> str:
    """Fetch failing CI logs for a branch, offloading to local LLM on RTX 5070 Ti if > 20KB."""
    if not shutil.which("gh"):
        return ""
    try:
        res = run_cmd(["gh", "run", "list", "--branch", branch_name, "--limit", "1", "--json", "databaseId,conclusion"], cwd=repo_path, check=False)
        runs = json.loads(res.stdout) if res.returncode == 0 and res.stdout.strip() else []
        if not runs or runs[0].get("conclusion") != "failure":
            return ""

        run_id = runs[0]["databaseId"]
        log_res = run_cmd(["gh", "run", "view", str(run_id), "--log-failed"], cwd=repo_path, check=False)
        raw_log = log_res.stdout.strip()

        if len(raw_log) > 20000:
            offload_script = Path("/home/federico/skills_library/scripts/local_llm_offload.py")
            if offload_script.exists():
                print("[OFFLOAD] Log exceeds 20KB; condensing error trace via local RTX 5070 Ti...")
                condense_res = run_cmd([
                    sys.executable, str(offload_script),
                    "--task", "log-extract",
                    "--prompt", "Extract exact error, failing tests, and file locations"
                ], input_str=raw_log, cwd=repo_path, check=False)
                if condense_res.returncode == 0 and condense_res.stdout.strip():
                    return condense_res.stdout.strip()

        return raw_log[:8000]
    except Exception as e:
        print(f"[WARN] Error fetching CI failure logs: {e}", file=sys.stderr)
        return ""


def find_suggestions(repo_path: Path, mode: str = "all", category: str = "all") -> List[Dict[str, Any]]:
    """Scan repository for concrete micro-improvements across Bolt, Palette, or Sentinel."""
    suggestions = []
    modes_to_scan = ["bolt", "palette", "sentinel"] if mode == "all" else [mode]
    ignore_dirs = {
        ".git", ".venv", "node_modules", "worktrees", ".worktrees", "__pycache__",
        "dist", "build", ".next", "coverage", ".turbo", ".cache", ".pytest_cache",
        ".stfolder", "data", "fixtures", "graphify-out"
    }

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith(".st")]
        for file in files:
            file_path = Path(root) / file
            rel_path = file_path.relative_to(repo_path)

            # Sentinel checks
            if "sentinel" in modes_to_scan and file.endswith((".py", ".ts", ".js", ".json")):
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                    for idx, line in enumerate(lines, 1):
                        if "shell=True" in line and "subprocess" in line:
                            suggestions.append({
                                "id": f"sentinel-{len(suggestions)+1}",
                                "persona": "sentinel",
                                "category": "security",
                                "title": "Avoid shell=True in subprocess calls",
                                "file": str(rel_path),
                                "line": idx,
                                "issue": "Passing shell=True introduces command injection risks if inputs are unsanitized.",
                                "impact": "Neutralizes shell injection vectors.",
                                "code_snippet": line.strip()
                            })
                        if any(k in line.lower() for k in ["secret_key =", "jwt_secret =", "default_password ="]) and any(w in line for w in ["'secret'", '"secret"', "'password'", '"password"', "'admin'"]):
                            suggestions.append({
                                "id": f"sentinel-{len(suggestions)+1}",
                                "persona": "sentinel",
                                "category": "security",
                                "title": "Hardcoded default credential or secret fallback",
                                "file": str(rel_path),
                                "line": idx,
                                "issue": "Hardcoded fallback credentials can be used as insecure defaults in production.",
                                "impact": "Enforces explicit secure environment configuration.",
                                "code_snippet": line.strip()
                            })
                        # SQL Injection in DDL
                        if any(stmt in line for stmt in ["CREATE DATABASE", "DROP DATABASE", "ALTER TABLE"]) and any(c in line for c in ["f\"", "f'", ".format(", "%s"]):
                            ddl_op = "CREATE DATABASE" if "CREATE DATABASE" in line else ("DROP DATABASE" if "DROP DATABASE" in line else "ALTER TABLE")
                            suggestions.append({
                                "id": f"sentinel-{len(suggestions)+1}",
                                "persona": "sentinel",
                                "category": "security",
                                "title": f"SQL Injection in {ddl_op}",
                                "file": str(rel_path),
                                "line": idx,
                                "issue": f"Dynamic string formatting in {ddl_op} bypasses parameterized queries.",
                                "impact": "Validate identifier with strict regex ^[a-zA-Z0-9_]+$ or quote securely.",
                                "code_snippet": line.strip()
                            })
                        # Overly permissive CORS
                        if "allow_origin_regex" in line and any(c in line for c in [r"\d{1,3}", "localhost"]):
                            suggestions.append({
                                "id": f"sentinel-{len(suggestions)+1}",
                                "persona": "sentinel",
                                "category": "security",
                                "title": "Overly Permissive CORS Regex",
                                "file": str(rel_path),
                                "line": idx,
                                "issue": "Matching broad local/private IP regex patterns in CORS can allow unauthorized cross-origin requests.",
                                "impact": "Restrict CORS explicitly to trusted origins.",
                                "code_snippet": line.strip()
                            })
                        # Empty except block
                        if line.strip().startswith("except Exception:") or line.strip() == "except:":
                            if idx < len(lines) and lines[idx].strip() in ["pass", "continue"]:
                                suggestions.append({
                                    "id": f"sentinel-{len(suggestions)+1}",
                                    "persona": "sentinel",
                                    "category": "security",
                                    "title": "Remove empty except Exception block",
                                    "file": str(rel_path),
                                    "line": idx,
                                    "issue": "Silently suppressing exceptions with pass hides underlying bugs and operational errors.",
                                    "impact": "Add logger warning or handle specific exception types.",
                                    "code_snippet": f"{line.strip()} {lines[idx].strip()}"
                                })
                except Exception:
                    pass

            # Palette checks (UX & Code Hygiene)
            if "palette" in modes_to_scan and file.endswith((".tsx", ".jsx", ".html", ".py")):
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                    for idx, line in enumerate(lines, 1):
                        if "<button" in line and not any(a in line for a in ["aria-label", "aria-labelledby"]):
                            sub_block = "".join(lines[idx-1:min(len(lines), idx+3)])
                            if any(ic in sub_block for ic in ["Icon", "Svg", "svg", "Trash", "Close", "Edit", "Plus", "Delete"]):
                                suggestions.append({
                                    "id": f"palette-{len(suggestions)+1}",
                                    "persona": "palette",
                                    "category": "hygiene",
                                    "title": "Icon-only button missing aria-label",
                                    "file": str(rel_path),
                                    "line": idx,
                                    "issue": "Screen readers cannot announce the purpose of buttons containing only icons.",
                                    "impact": "Improves WCAG compliance and accessibility for assistive technology.",
                                    "code_snippet": line.strip()
                                })
                        if line.strip() == "pass" and idx > 1:
                            prev = lines[idx-2].strip()
                            if any(prev.endswith(k) for k in [":", "return", "pass"]):
                                suggestions.append({
                                    "id": f"palette-{len(suggestions)+1}",
                                    "persona": "palette",
                                    "category": "hygiene",
                                    "title": f"Remove empty pass block in {file_path.stem}",
                                    "file": str(rel_path),
                                    "line": idx,
                                    "issue": "Redundant pass statement can be removed for cleaner code.",
                                    "impact": "Improves code hygiene and readability.",
                                    "code_snippet": f"{prev} -> pass"
                                })
                except Exception:
                    pass

            # Bolt checks (Performance)
            if "bolt" in modes_to_scan and file.endswith((".py", ".ts", ".js")):
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                    for idx, line in enumerate(lines, 1):
                        if "strptime(" in line and any("for " in lines[max(0, idx-4):idx][i] for i in range(len(lines[max(0, idx-4):idx]))):
                            suggestions.append({
                                "id": f"bolt-{len(suggestions)+1}",
                                "persona": "bolt",
                                "category": "performance",
                                "title": "Repeated datetime.strptime inside loop",
                                "file": str(rel_path),
                                "line": idx,
                                "issue": "datetime.strptime introduces heavy parsing overhead when called repeatedly inside loops.",
                                "impact": "Pre-computing or replacing with fromisoformat yields a 4x-5x speedup.",
                                "code_snippet": line.strip()
                            })
                        # N+1 queries in loops
                        if "for " in line and any(k in line for k in [" in ", ":"]):
                            loop_block = "".join(lines[idx:min(len(lines), idx+6)])
                            if any(q in loop_block for q in ["db.query(", "session.query("]) and any(op in loop_block for op in [".delete(", ".all()", ".first()"]):
                                if not any(b in loop_block for b in ["bulk_", ".in_("]):
                                    suggestions.append({
                                        "id": f"bolt-{len(suggestions)+1}",
                                        "persona": "bolt",
                                        "category": "performance",
                                        "title": f"N+1 Query in {file_path.stem}",
                                        "file": str(rel_path),
                                        "line": idx,
                                        "issue": "Database query executed inside iteration loop causes repeated network/DB roundtrips.",
                                        "impact": "Consolidate into a single bulk query with in_() for 10x-100x speedup.",
                                        "code_snippet": line.strip()
                                    })
                        # Suboptimal loop finding item in list
                        if "for " in line and any(k in line for k in [" in ", ":"]):
                            loop_block = "".join(lines[idx:min(len(lines), idx+3)])
                            if "if " in loop_block and any(op in loop_block for op in ["==", "is "]) and "return " in loop_block:
                                suggestions.append({
                                    "id": f"bolt-{len(suggestions)+1}",
                                    "persona": "bolt",
                                    "category": "performance",
                                    "title": "Suboptimal Loop Finding Item in List",
                                    "file": str(rel_path),
                                    "line": idx,
                                    "issue": "Iterating linearly over a collection to return a single match can be replaced with next() or dictionary lookup.",
                                    "impact": "Reduces O(n) scan to O(1) dictionary retrieval or concise generator.",
                                    "code_snippet": line.strip()
                                })
                except Exception:
                    pass

    # Test Gap Scanner (Palette / Craftsman)
    if any(m in modes_to_scan for m in ["palette", "bolt", "sentinel"]):
        tests_dir = repo_path / "tests"
        if tests_dir.exists():
            test_stems = {f.stem.replace("test_", "") for f in tests_dir.rglob("test_*.py")}
            # Check modules in src/ and apps/api/
            for check_dir_name in ["src", "apps/api/routers", "apps/api/services"]:
                target_check_dir = repo_path / check_dir_name
                if target_check_dir.exists():
                    for src_file in target_check_dir.rglob("*.py"):
                        if src_file.name.startswith("__"):
                            continue
                        stem = src_file.stem
                        if stem not in test_stems and f"test_{stem}" not in test_stems:
                            rel_src = src_file.relative_to(repo_path)
                            suggestions.append({
                                "id": f"craftsman-{len(suggestions)+1}",
                                "persona": "palette",
                                "category": "tests",
                                "title": f"Missing test file for {src_file.name}",
                                "file": str(rel_src),
                                "line": 1,
                                "issue": f"Module {src_file.name} lacks a dedicated unit test suite in tests/.",
                                "impact": "Ensures regression safety and automated test coverage.",
                                "code_snippet": f"tests/test_{stem}.py"
                            })
    if category != "all":
        suggestions = [s for s in suggestions if s.get("category") == category]

    return suggestions


def resolve_project_path(repo_query: str) -> Path:
    """Resolve project name or path against projects_registry.json or direct path."""
    direct_path = Path(repo_query).expanduser().resolve()
    if direct_path.exists() and (direct_path / ".git").exists():
        return direct_path

    if PROJECTS_REGISTRY.exists():
        try:
            with open(PROJECTS_REGISTRY, "r", encoding="utf-8") as f:
                data = json.load(f)
            projects = (
                data.get("projects", []) if isinstance(data, dict) else data
            )
            for p in projects:
                name = p.get("name", "").lower()
                p_path = Path(p.get("path", "")).expanduser().resolve()
                if (
                    name == repo_query.lower()
                    or p_path.name.lower() == repo_query.lower()
                ):
                    if p_path.exists() and (p_path / ".git").exists():
                        return p_path
        except Exception as e:
            print(
                f"[WARN] Error reading {PROJECTS_REGISTRY}: {e}",
                file=sys.stderr,
            )

    raise ValueError(
        f"Could not resolve '{repo_query}' to an existing git repository."
    )


def list_registered_repos() -> List[Dict[str, str]]:
    """Return all valid git repositories registered in projects_registry.json."""
    results = []
    if not PROJECTS_REGISTRY.exists():
        return results

    try:
        with open(PROJECTS_REGISTRY, "r", encoding="utf-8") as f:
            data = json.load(f)
        projects = data.get("projects", []) if isinstance(data, dict) else data
        for p in projects:
            p_path = Path(p.get("path", "")).expanduser().resolve()
            if p_path.exists() and (p_path / ".git").exists():
                results.append(
                    {
                        "name": p.get("name", p_path.name),
                        "path": str(p_path),
                        "description": (p.get("description") or "")[:80],
                    }
                )
    except Exception as e:
        print(f"[WARN] Could not parse projects: {e}", file=sys.stderr)
    return results


class WorktreeSession:
    """Context manager handling creation and cleanup of isolated git worktrees."""

    def __init__(self, repo_path: Path, mode: str, branch_name: Optional[str] = None):
        self.repo_path = repo_path
        self.mode = mode
        now_str = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        self.branch_name = branch_name or f"curator/{mode}-{now_str}"
        self.slug = f"{repo_path.name}-{mode}"
        self.worktree_path = WORKTREES_DIR / self.slug

    def __enter__(self) -> Tuple[Path, str]:
        WORKTREES_DIR.mkdir(parents=True, exist_ok=True)
        # Prune dead worktrees first
        run_cmd(["git", "worktree", "prune"], cwd=self.repo_path, check=False)

        # If previous worktree exists for this slug, clean it
        if self.worktree_path.exists():
            print(f"[INFO] Removing previous worktree at {self.worktree_path}")
            run_cmd(
                ["git", "worktree", "remove", "--force", str(self.worktree_path)],
                cwd=self.repo_path,
                check=False,
            )
            shutil.rmtree(self.worktree_path, ignore_errors=True)

        print(f"[INFO] Creating isolated worktree for '{self.repo_path.name}' at:")
        print(f"       -> {self.worktree_path}")
        print(f"       -> Branch: {self.branch_name}")

        # Check if branch exists locally or on remote
        branch_check = run_cmd(["git", "show-ref", "--verify", f"refs/heads/{self.branch_name}"], cwd=self.repo_path, check=False)
        if branch_check.returncode == 0:
            run_cmd(["git", "worktree", "add", str(self.worktree_path), self.branch_name], cwd=self.repo_path)
        else:
            remote_check = run_cmd(["git", "show-ref", "--verify", f"refs/remotes/origin/{self.branch_name}"], cwd=self.repo_path, check=False)
            if remote_check.returncode == 0:
                run_cmd(["git", "worktree", "add", "-b", self.branch_name, str(self.worktree_path), f"origin/{self.branch_name}"], cwd=self.repo_path)
            else:
                run_cmd(["git", "worktree", "add", "-b", self.branch_name, str(self.worktree_path), "HEAD"], cwd=self.repo_path)

        # Link shared large dependencies from parent repo into worktree if present
        for dep_name in [".venv", "node_modules", ".env"]:
            parent_dep = self.repo_path / dep_name
            target_dep = self.worktree_path / dep_name
            if parent_dep.exists() and not target_dep.exists():
                try:
                    os.symlink(parent_dep, target_dep)
                except Exception as e:
                    print(f"[WARN] Could not symlink {dep_name}: {e}", file=sys.stderr)

        return self.worktree_path, self.branch_name

    def __exit__(self, exc_type, exc_val, exc_tb):
        # We do not automatically delete if a successful commit occurred unless explicitly requested
        pass


def detect_test_command(worktree_path: Path) -> Optional[List[str]]:
    """Autodetect the fastest local test command for the repository."""
    # 1. Custom repo script
    fast_tests = worktree_path / "run_fast_tests.sh"
    if fast_tests.exists() and os.access(fast_tests, os.X_OK):
        return ["./run_fast_tests.sh"]

    # 2. Node / Next.js
    pkg_json = worktree_path / "package.json"
    if pkg_json.exists():
        try:
            with open(pkg_json, "r", encoding="utf-8") as f:
                pkg_data = json.load(f)
            scripts = pkg_data.get("scripts", {})
            if "test" in scripts:
                return ["pnpm", "test"] if (worktree_path / "pnpm-lock.yaml").exists() else ["npm", "test"]
            if "typecheck" in scripts:
                return ["npm", "run", "typecheck"]
        except Exception:
            pass

    # 3. Python pytest
    if (worktree_path / "pyproject.toml").exists() or (worktree_path / "pytest.ini").exists() or (worktree_path / "tests").exists():
        if (worktree_path / ".venv" / "bin" / "pytest").exists():
            return [str(worktree_path / ".venv" / "bin" / "pytest"), "-q", "--tb=short", "--maxfail=2"]
        return ["uv", "run", "pytest", "-q", "--tb=short", "--maxfail=2"]

    return None


def run_tests_in_worktree(worktree_path: Path) -> Tuple[bool, str]:
    """Execute tests in worktree and return success status and output."""
    test_cmd = detect_test_command(worktree_path)
    if not test_cmd:
        return True, "No automated test suite detected. Skipping test gate."

    print(f"[TEST] Executing in worktree: {' '.join(test_cmd)}")
    res = run_cmd(test_cmd, cwd=worktree_path, check=False)
    output = (res.stdout + "\n" + res.stderr).strip()
    return (res.returncode == 0), output


def cleanup_all_worktrees() -> None:
    """Prune and remove all worktrees managed by Jules."""
    if not WORKTREES_DIR.exists():
        print("[INFO] No worktrees directory found.")
        return

    print(f"[INFO] Cleaning up worktrees in {WORKTREES_DIR}...")
    for item in WORKTREES_DIR.iterdir():
        if item.is_dir():
            print(f" -> Removing {item.name}")
            shutil.rmtree(item, ignore_errors=True)

    # Prune from all known repos
    for repo in list_registered_repos():
        p = Path(repo["path"])
        run_cmd(["git", "worktree", "prune"], cwd=p, check=False)
    print("[SUCCESS] All worktrees cleaned and pruned.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Jules Curator Hub: Autonomous worktree optimizer (Bolt, Palette, Sentinel)"
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Subcommand")

    # Command: run
    run_parser = subparsers.add_parser("run", help="Run curator persona on a repository")
    run_parser.add_argument(
        "--repo", "-r", required=True, help="Repository name or path (e.g. RoosterLab, ag2r)"
    )
    run_parser.add_argument(
        "--mode",
        "-m",
        required=True,
        choices=["bolt", "palette", "sentinel"],
        help="Curator mode: bolt (performance), palette (UX/a11y), sentinel (security)",
    )
    run_parser.add_argument(
        "--branch", "-b", default=None, help="Custom branch name for isolated worktree"
    )
    run_parser.add_argument(
        "--dry-run", action="store_true", help="Inspect and report without committing"
    )

    # Command: knowledge
    know_parser = subparsers.add_parser("knowledge", help="Display accumulated knowledge for a repository")
    know_parser.add_argument("--repo", "-r", required=True, help="Repository name or path")
    know_parser.add_argument("--mode", "-m", choices=["bolt", "palette", "sentinel"], help="Filter by persona mode")

    # Command: record-learning
    rec_parser = subparsers.add_parser("record-learning", help="Record a new critical learning into knowledge base")
    rec_parser.add_argument("--repo", "-r", required=True, help="Repository name or path")
    rec_parser.add_argument("--mode", "-m", required=True, choices=["bolt", "palette", "sentinel"], help="Curator mode")
    rec_parser.add_argument("--title", "-t", required=True, help="Title of the learning")
    rec_parser.add_argument("--learning", "-l", required=True, help="Insight / vulnerability description")
    rec_parser.add_argument("--action", "-a", required=True, help="Action / prevention guideline for next time")

    # Command: fix-ci
    fix_parser = subparsers.add_parser("fix-ci", help="Auto-fix failing CI checks on a pull request")
    fix_parser.add_argument("--repo", "-r", required=True, help="Repository name or path")
    fix_parser.add_argument("--pr", "-p", type=int, default=None, help="Pull Request number (optional)")
    fix_parser.add_argument("--branch", "-b", default=None, help="Branch name if fixing without PR number")
    fix_parser.add_argument("--max-rounds", type=int, default=2, help="Max auto-fix rounds (default: 2)")

    # Command: suggest
    sug_parser = subparsers.add_parser("suggest", help="Scan for issues and prompt to confirm each fix (Jules Suggestions)")
    sug_parser.add_argument("--repo", "-r", required=True, help="Repository name or path")
    sug_parser.add_argument("--mode", "-m", choices=["all", "bolt", "palette", "sentinel"], default="all", help="Curator mode (default: all)")
    sug_parser.add_argument(
        "--category",
        "-c",
        choices=["all", "security", "performance", "hygiene", "tests"],
        default="all",
        help="Filter suggestions by category (default: all)",
    )
    sug_parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=None,
        help="Limit the number of suggestions displayed/applied",
    )
    sug_parser.add_argument("--json", action="store_true", help="Output suggestions in JSON format for Antigravity UI")

    # Command: list
    subparsers.add_parser("list", help="List registered repositories available for curator")

    # Command: cleanup
    subparsers.add_parser("cleanup", help="Clean up and prune all active worktrees")

    # Command: status
    subparsers.add_parser("status", help="Show active worktrees status")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.subcommand == "knowledge":
        repo_path = resolve_project_path(args.repo)
        modes = [args.mode] if args.mode else ["bolt", "palette", "sentinel"]
        print(f"\n🧠 Accumulated Knowledge for '{repo_path.name}':")
        print("─" * 70)
        found_any = False
        for m in modes:
            entries = load_knowledge(repo_path, m)
            if entries:
                found_any = True
                persona = PERSONAS[m]
                print(f"\n[{persona['name']}] ({len(entries)} entries):")
                for e in entries:
                    print(f" • {e.get('header', 'Untitled')} (from {e.get('source', 'unknown')})")
                    if "text" in e:
                        for line in e["text"].splitlines()[:3]:
                            print(f"   {line}")
        if not found_any:
            print(" [INFO] No prior knowledge entries recorded yet.")
        print("─" * 70)
        return

    if args.subcommand == "record-learning":
        repo_path = resolve_project_path(args.repo)
        record_learning(repo_path, args.mode, args.title, args.learning, args.action)
        return

    if args.subcommand == "list":
        repos = list_registered_repos()
        print(f"\n📁 Registered Repositories ({len(repos)} found):")
        print("─" * 70)
        for r in repos:
            print(f" • {r['name']:<18} | {r['path']}")
            if r["description"]:
                print(f"   └─ {r['description']}")
        print("─" * 70)
        return

    if args.subcommand == "cleanup":
        cleanup_all_worktrees()
        return

    if args.subcommand == "status":
        if not WORKTREES_DIR.exists() or not any(WORKTREES_DIR.iterdir()):
            print("[INFO] No active worktrees currently in Jules Hub.")
            return
        print(f"\n🌳 Active Worktrees in {WORKTREES_DIR}:")
        for item in WORKTREES_DIR.iterdir():
            if item.is_dir():
                # Check git branch
                res = run_cmd(["git", "branch", "--show-current"], cwd=item, check=False)
                branch = res.stdout.strip() or "detached"
                print(f" • {item.name:<25} [branch: {branch}]")
        return

    if args.subcommand == "fix-ci":
        repo_path = resolve_project_path(args.repo)
        print("=" * 70)
        print("🛠️ JULES CURATOR: CI Auto-Fixer Loop (Beta)")
        print(f"📁 Target Repository: {repo_path}")
        print("=" * 70)

        pr_data = get_failing_pr(repo_path, args.pr)
        if not pr_data:
            print("[INFO] Could not find any open PR or PR checks to inspect.")
            return

        pr_num = pr_data.get("number")
        branch_name = args.branch or pr_data.get("headRefName")
        title = pr_data.get("title", "")
        failing_checks = pr_data.get("failing_checks", [])

        print(f"\n🔍 PR #{pr_num}: '{title}'")
        print(f"🌿 Head Branch: {branch_name}")

        if not failing_checks:
            print("✅ All CI checks on GitHub are currently passing! No auto-fix needed.")
            return

        print(f"\n❌ Detected {len(failing_checks)} failing CI check(s):")
        for fc in failing_checks:
            print(f"   • {fc.get('name')} [{fc.get('state')}]")

        print(f"\n📥 Fetching failing CI logs...")
        err_log = fetch_ci_failure_log(repo_path, branch_name)
        if err_log:
            print("\n📋 CI Failure Traceback Summary:")
            for line in err_log.splitlines()[:15]:
                print(f"   {line}")
            if len(err_log.splitlines()) > 15:
                print("   ...")

        with WorktreeSession(repo_path, "ci-fix", branch_name=branch_name) as (worktree, branch):
            print(f"\n✨ Isolated worktree created for CI Auto-Fix at:\n   {worktree}")
            print(f"🌿 Branch: {branch}")
            print("\n⚙️ Auto-Fix Instructions for Agent:")
            print("   1. Reproduce the failure with local test runner.")
            print("   2. Apply targeted fix (< 50 lines) without breaking other behavior.")
            print("   3. Run tests locally; when GREEN, commit and push to remote:")
            print(f"      git commit -am \"fix(ci): auto-fix failing check on PR #{pr_num}\"")
            print(f"      git push origin {branch}")
            print("=" * 70)
            return

    if args.subcommand == "suggest":
        repo_path = resolve_project_path(args.repo)
        suggestions = find_suggestions(repo_path, args.mode, category=args.category)

        if args.limit is not None and args.limit > 0:
            suggestions = suggestions[:args.limit]

        if args.json:
            print(json.dumps(suggestions, indent=2))
            return

        print("=" * 70)
        print(f"💡 JULES SUGGESTIONS ENGINE: '{repo_path.name}'")
        print(f"🔍 Mode: {args.mode.upper()}")
        print(f"🎯 Category: {args.category.upper()}")
        if args.limit:
            print(f"🔢 Limit: {args.limit}")
        print("=" * 70)

        if not suggestions:
            print("\n✨ Clean codebase! No candidate issues found for the selected criteria.")
            print("=" * 70)
            return

        print(f"\n🎯 Found {len(suggestions)} potential improvement suggestion(s):\n")
        applied_count = 0

        for idx, sug in enumerate(suggestions, 1):
            persona_info = PERSONAS.get(sug["persona"], {"name": sug["persona"].capitalize(), "icon": "💡"})
            print("─" * 70)
            print(f"[{idx}/{len(suggestions)}] {persona_info['icon']} {sug['title']}")
            print(f"📁 Location: {sug['file']}:{sug['line']}")
            print(f"⚠️  Issue:    {sug['issue']}")
            print(f"📈 Impact:   {sug['impact']}")
            print(f"💻 Code:     {sug['code_snippet']}")
            print("─" * 70)

            if sys.stdin.isatty():
                ans = input("Prompt to confirm: Apply this fix in isolated worktree? [y/N/s(kip)/q(uit)]: ").strip().lower()
                if ans == "q":
                    print("[ABORT] Exiting suggestions prompt.")
                    break
                if ans == "y":
                    applied_count += 1
                    branch_name = f"curator/suggest-{sug['persona']}-{idx}"
                    print(f"\n[ACTION] Spawning isolated worktree on branch '{branch_name}'...")
                    with WorktreeSession(repo_path, f"sug-{sug['persona']}", branch_name=branch_name) as (worktree, branch):
                        print(f"✨ Worktree active at: {worktree}")
                        print("👉 Sub-agent or developer can now apply the patch and run tests.")
                else:
                    print("[SKIPPED] Moving to next suggestion.")
            else:
                print("ℹ️  Interactive mode available via terminal or Antigravity ask_question modal.")

        print("\n" + "=" * 70)
        print(f"🏁 Suggestions scan complete. Total: {len(suggestions)}, Applied: {applied_count}")
        print("=" * 70)
        return

    if args.subcommand == "run":
        repo_path = resolve_project_path(args.repo)
        persona = PERSONAS[args.mode]

        print("=" * 70)
        print(f"🎯 JULES CURATOR RUNNER: {persona['name']}")
        print(f"📁 Target Repository: {repo_path}")
        print(f"📜 Mission: {persona['mission']}")
        print("=" * 70)

        # Inject Knowledge
        knowledge_entries = load_knowledge(repo_path, args.mode)
        if knowledge_entries:
            print(f"\n🧠 [KNOWLEDGE BASE INJECTED: {len(knowledge_entries)} Past Learnings Active]")
            for idx, k in enumerate(knowledge_entries[:4], 1):
                print(f"   {idx}. {k.get('header', 'Insight')}")
            if len(knowledge_entries) > 4:
                print(f"   ... and {len(knowledge_entries) - 4} more learnings active.")

        with WorktreeSession(repo_path, args.mode, args.branch) as (worktree, branch):
            # Run baseline tests
            print("\n🔍 Running baseline tests to verify clean state...")
            passed, test_out = run_tests_in_worktree(worktree)
            if not passed:
                print(f"[ERROR] Baseline tests failed in clean worktree:\n{test_out}", file=sys.stderr)
                print("[ABORT] Cannot optimize repository with failing baseline tests.")
                sys.exit(1)
            print("✅ Baseline tests passed.")

            print(f"\n✨ Isolated worktree is ready at:\n   {worktree}")
            print(f"🌿 Branch: {branch}")
            print("\n📋 Taxonomy Checklist to scan:")
            for item in persona["focus"]:
                print(f"   • [ ] {item}")

            print("\n⚠️ Boundaries:")
            print("   • Hard ceiling: < 50 lines modified.")
            print("   • Preserves existing behavior and readability.")
            print("   • Zero-noise rule: If no clear win is found, stop cleanly.")
            print("=" * 70)

            # Output instructions for subagent / runner
            print(f"\n[READY] Sub-agents or master can now inspect '{worktree}' in total isolation.")
            return

    parser.print_help()


if __name__ == "__main__":
    main()
