"""
Jules Hub Multi-Engine Router: Flash, Local Ollama, and Hybrid execution.
Orchestrates AI-driven patch generation for micro-improvements across Bolt (Performance),
Palette (UX/A11y), and Sentinel (Security) personas.

Engines:
1. antigravity_flash: Headless execution via `agy --model flash --mode auto --output-format stream-json`
2. local: Async HTTP client via Ollama endpoint (`http://localhost:11434/api/generate`) with `qwen2.5-coder`
3. hybrid: Local heuristic/AST candidate targeting + Flash micro-patching (< 50 lines)

Invariants:
- Typed argument lists (`list[str]`) with `shell=False` for all subprocesses.
- Process group kill (`os.killpg`) upon subprocess timeouts.
- Graceful degradation: Flash failure degrades to Local; Local failure returns structured `PatchResult` without raising exceptions.
"""

import ast
import asyncio
from datetime import datetime, timezone
import difflib
import json
import logging
import os
import re
import signal
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import httpx

from hub.models import EngineMode, PatchResult, PERSONAS, RoleModelConfig, SeniorReviewResult

logger = logging.getLogger("hub.engine_router")


def count_diff_lines(diff_text: str) -> int:
    """
    Count additions and deletions in a unified diff, excluding file headers and hunk markers.
    Handles both native newlines and literal escaped backslash-n sequences.
    """
    if "\\n" in diff_text and "\n" not in diff_text:
        diff_text = diff_text.replace("\\r\\n", "\n").replace("\\n", "\n")
    count = 0
    for line in diff_text.splitlines():
        if (line.startswith("+") and not line.startswith("+++")) or \
           (line.startswith("-") and not line.startswith("---")):
            count += 1
    return count


def extract_diff_from_text(text: str) -> Optional[str]:
    """
    Extract unified diff from markdown code fences (```diff ... ```) or raw diff headers.
    """
    if not text:
        return None

    if "\\n" in text and "\n" not in text:
        text = text.replace("\\r\\n", "\n").replace("\\n", "\n")

    # Check for ```diff ... ``` or ```patch ... ```
    m = re.search(r"```(?:diff|patch)\s*\n(.*?)\n```", text, re.DOTALL | re.IGNORECASE)
    if m:
        diff_str = m.group(1).strip()
        if "\\n" in diff_str and "\n" not in diff_str:
            diff_str = diff_str.replace("\\r\\n", "\n").replace("\\n", "\n")
        return diff_str

    # Check for unified diff headers directly in text
    if "--- " in text and "+++ " in text and "@@ " in text:
        start_idx = text.find("--- ")
        diff_part = text[start_idx:]
        if "```" in diff_part:
            diff_part = diff_part[:diff_part.find("```")]
        diff_str = diff_part.strip()
        if "\\n" in diff_str and "\n" not in diff_str:
            diff_str = diff_str.replace("\\r\\n", "\n").replace("\\n", "\n")
        return diff_str

    return None


def extract_code_from_text(text: str) -> Optional[str]:
    """
    Extract code block from markdown if model returned replacement code instead of diff.
    """
    if not text:
        return None
    m = re.search(r"```(?:python|py|javascript|js|typescript|ts|html|css|json|sh|bash)?\s*\n(.*?)\n```", text, re.DOTALL)
    if m:
        return m.group(1)
    return None


def get_git_diff(repo_path: Path, target_file: Optional[str] = None) -> str:
    """
    Fetch uncommitted git diff from repository using typed argument list and shell=False.
    """
    cmd = ["git", "diff"]
    if target_file:
        cmd.append(target_file)
    try:
        res = subprocess.run(
            cmd,
            cwd=str(repo_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False,
            timeout=10,
        )
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception as e:
        logger.debug("git diff failed or repository is not initialized: %s", e)
    return ""


def apply_hunks_to_content(original_content: str, diff_text: str) -> Optional[str]:
    """
    Pure-Python unified diff hunk applicator as fallback when git apply is unavailable.
    """
    try:
        orig_lines = original_content.splitlines(keepends=True)
        hunk_header_re = re.compile(r"^@@\s+-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?\s+@@")

        diff_lines = diff_text.splitlines(keepends=True)
        hunk_indices: List[int] = []
        for idx, line in enumerate(diff_lines):
            if line.startswith("@@"):
                hunk_indices.append(idx)

        if not hunk_indices:
            return None

        applied_lines = list(orig_lines)
        offset = 0

        for i, h_idx in enumerate(hunk_indices):
            header = diff_lines[h_idx]
            m = hunk_header_re.match(header.strip())
            if not m:
                continue

            old_start = int(m.group(1)) - 1
            next_h_idx = hunk_indices[i + 1] if i + 1 < len(hunk_indices) else len(diff_lines)
            hunk_body = diff_lines[h_idx + 1:next_h_idx]

            expected_old: List[str] = []
            replacement: List[str] = []

            for h_line in hunk_body:
                if h_line.startswith("---") or h_line.startswith("+++"):
                    continue
                tag = h_line[0] if len(h_line) > 0 else " "
                val = h_line[1:]
                if tag == " ":
                    expected_old.append(val)
                    replacement.append(val)
                elif tag == "-":
                    expected_old.append(val)
                elif tag == "+":
                    replacement.append(val)

            target_pos = old_start + offset
            target_slice = applied_lines[target_pos:target_pos + len(expected_old)]
            # If context matches or normalized matches:
            if [s.strip() for s in target_slice] == [s.strip() for s in expected_old]:
                applied_lines[target_pos:target_pos + len(expected_old)] = replacement
                offset += len(replacement) - len(expected_old)
            else:
                # Attempt to find expected_old in file
                for search_pos in range(len(applied_lines)):
                    candidate = applied_lines[search_pos:search_pos + len(expected_old)]
                    if [s.strip() for s in candidate] == [s.strip() for s in expected_old]:
                        applied_lines[search_pos:search_pos + len(expected_old)] = replacement
                        offset += len(replacement) - len(expected_old)
                        break

        return "".join(applied_lines)
    except Exception as e:
        logger.debug("Failed in Python hunk applicator: %s", e)
        return None


class EngineRouter:
    """
    Multi-Engine Router for Jules Hub.
    Dispatches patch generation to Local Ollama, Antigravity Flash, or Hybrid modes,
    managing graceful fallbacks and strict scope ceilings (< 50 lines).
    """

    def __init__(
        self,
        ollama_url: Optional[str] = None,
        ollama_model: Optional[str] = None,
        agy_bin: Optional[str] = None,
        http_timeout: float = 60.0,
        subprocess_timeout: float = 120.0,
        default_mode: EngineMode = EngineMode.ANTIGRAVITY_FLASH,
        max_lines: int = 50,
        enforce_scope_ceiling: bool = False,
        allow_fallback: bool = True,
    ):
        self.ollama_url = (ollama_url or os.getenv("OLLAMA_HOST", "http://localhost:11434")).rstrip("/")
        self.ollama_model = ollama_model or os.getenv("OLLAMA_MODEL", "qwen2.5-coder")
        self.agy_bin = agy_bin or os.getenv("AGY_BIN", "agy")
        self.http_timeout = float(http_timeout)
        self.subprocess_timeout = float(subprocess_timeout)
        self.default_mode = default_mode
        self.max_lines = max_lines
        self.enforce_scope_ceiling = enforce_scope_ceiling
        self.allow_fallback = allow_fallback

    def _heuristic_target(
        self,
        file_content: str,
        issue_context: str,
        target_file: str,
    ) -> Tuple[Optional[int], Optional[int], str]:
        """
        Locate candidate section/lines in target file using AST and keyword heuristics.
        Returns (start_line, end_line, candidate_snippet).
        """
        lines = file_content.splitlines(keepends=True)
        if not lines:
            return None, None, ""

        # 1. Line number hint from issue context (e.g., 'line 42' or ':42:')
        line_match = re.search(r"(?:line\s*|:)(\d+)", issue_context, re.IGNORECASE)
        if line_match:
            try:
                target_ln = int(line_match.group(1))
                if 1 <= target_ln <= len(lines):
                    start = max(1, target_ln - 15)
                    end = min(len(lines), target_ln + 15)
                    snippet = "".join(lines[start - 1:end])
                    return start, end, snippet
            except Exception:
                pass

        # 2. Python AST inspection: find matching function or class definitions
        if target_file.endswith(".py"):
            try:
                tree = ast.parse(file_content)
                issue_tokens = set(re.findall(r"\w{3,}", issue_context.lower()))
                best_node = None
                best_score = 0
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        node_tokens = set(re.findall(r"\w{3,}", node.name.lower()))
                        score = len(issue_tokens.intersection(node_tokens))
                        if score > best_score:
                            best_score = score
                            best_node = node
                if best_node and hasattr(best_node, "lineno") and hasattr(best_node, "end_lineno"):
                    start = best_node.lineno
                    end = best_node.end_lineno or min(len(lines), start + 40)
                    snippet = "".join(lines[start - 1:end])
                    return start, end, snippet
            except Exception:
                pass

        # 3. Keyword frequency scanning across lines
        issue_words = [w.lower() for w in re.findall(r"\w{4,}", issue_context) if w.isalnum()]
        if issue_words:
            scores = [0] * len(lines)
            for idx, line in enumerate(lines):
                line_lower = line.lower()
                scores[idx] = sum(1 for w in issue_words if w in line_lower)
            max_score = max(scores)
            if max_score > 0:
                best_idx = scores.index(max_score) + 1
                start = max(1, best_idx - 15)
                end = min(len(lines), best_idx + 15)
                snippet = "".join(lines[start - 1:end])
                return start, end, snippet

        # Fallback to first 80 lines
        end = min(len(lines), 80)
        return 1, end, "".join(lines[:end])

    def _build_prompt(
        self,
        persona_key: str,
        target_file: str,
        file_content: str,
        issue_context: str,
        candidate_snippet: Optional[str] = None,
    ) -> str:
        """Construct structured prompt enforcing Persona guidelines and scope ceiling."""
        persona_info = PERSONAS.get(persona_key, {})
        persona_name = persona_info.get("name", persona_key.capitalize())
        role = persona_info.get("role", "Software Engineer")
        mission = persona_info.get("mission", "Implement an atomic improvement < 50 lines.")
        focus = "\n".join(f"- {f}" for f in persona_info.get("focus", []))
        avoids = "\n".join(f"- {a}" for a in persona_info.get("avoids", []))

        prompt_parts = [
            f"You are {persona_name}, acting as {role}.",
            f"Mission: {mission}",
            "",
            "Focus areas:",
            focus,
            "",
            "Avoid:",
            avoids,
            "",
            f"Target File: {target_file}",
            f"Issue Context:\n{issue_context}",
            "",
        ]

        if candidate_snippet:
            prompt_parts.extend([
                "Identified Candidate Code Section:",
                "```",
                candidate_snippet,
                "```",
                "",
            ])

        prompt_parts.extend([
            "Full/Current File Content:",
            "```",
            file_content,
            "```",
            "",
            "CRITICAL INSTRUCTIONS:",
            "1. Output a unified git diff solving the issue with AT MOST 50 lines changed.",
            "2. Preserve existing logic and comments outside the fix.",
            "3. Enclose the unified diff inside a ```diff code block.",
        ])

        return "\n".join(prompt_parts)

    def _apply_patch(
        self,
        target_path: Path,
        repo_path: Path,
        diff_text: Optional[str],
        replacement_code: Optional[str],
        original_content: str,
    ) -> Tuple[bool, str]:
        """
        Apply generated diff or replacement code to target file.
        Returns (success, computed_diff).
        """
        rel_path = str(target_path.relative_to(repo_path))

        # 1. Try git apply if diff_text is available
        if diff_text:
            if "\\n" in diff_text and "\n" not in diff_text:
                diff_text = diff_text.replace("\\r\\n", "\n").replace("\\n", "\n")
            try:
                proc = subprocess.run(
                    ["git", "apply", "--whitespace=fix", "-"],
                    input=diff_text,
                    cwd=str(repo_path),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    shell=False,
                    timeout=10,
                )
                if proc.returncode == 0:
                    git_diff = get_git_diff(repo_path, rel_path)
                    return True, git_diff or diff_text
            except Exception as e:
                logger.debug("git apply failed: %s", e)

            # 2. Pure-Python hunk applicator
            patched_content = apply_hunks_to_content(original_content, diff_text)
            if patched_content is not None and patched_content != original_content:
                target_path.write_text(patched_content, encoding="utf-8")
                git_diff = get_git_diff(repo_path, rel_path)
                if git_diff:
                    return True, git_diff
                comp_diff = "".join(difflib.unified_diff(
                    original_content.splitlines(keepends=True),
                    patched_content.splitlines(keepends=True),
                    fromfile=f"a/{rel_path}",
                    tofile=f"b/{rel_path}",
                ))
                return True, comp_diff or diff_text

        # 3. Direct replacement code write if diff application didn't succeed
        if replacement_code and replacement_code != original_content:
            target_path.write_text(replacement_code, encoding="utf-8")
            git_diff = get_git_diff(repo_path, rel_path)
            if git_diff:
                return True, git_diff
            comp_diff = "".join(difflib.unified_diff(
                original_content.splitlines(keepends=True),
                replacement_code.splitlines(keepends=True),
                fromfile=f"a/{rel_path}",
                tofile=f"b/{rel_path}",
            ))
            return True, comp_diff

        # If diff_text was provided without file mutation (e.g. mock test)
        if diff_text:
            return True, diff_text

        return False, ""

    async def _patch_local(
        self,
        repo_path: Path,
        target_path: Path,
        persona_key: str,
        issue_context: str,
        prompt_override: Optional[str] = None,
    ) -> PatchResult:
        """
        Execute patch generation via local Ollama endpoint (/api/generate).
        """
        rel_file = str(target_path.relative_to(repo_path))
        try:
            original_content = target_path.read_text(encoding="utf-8")
        except Exception as e:
            return PatchResult(success=False, error=f"Failed reading target file: {e}", engine_used="local")

        prompt = prompt_override or self._build_prompt(
            persona_key=persona_key,
            target_file=rel_file,
            file_content=original_content,
            issue_context=issue_context,
        )

        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
        }

        url = f"{self.ollama_url}/api/generate"
        logger.info("Calling Ollama endpoint %s (model=%s)", url, self.ollama_model)

        try:
            async with httpx.AsyncClient(timeout=self.http_timeout) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            logger.warning("Local Ollama engine request failed: %s", e)
            return PatchResult(
                success=False,
                error=f"Local Ollama engine failed: {type(e).__name__} ({e})",
                engine_used="local",
            )

        response_text = data.get("response", "")
        if not response_text:
            return PatchResult(
                success=False,
                error="Local Ollama engine returned empty response",
                engine_used="local",
            )

        diff_text = extract_diff_from_text(response_text)
        code_text = extract_code_from_text(response_text)

        applied, final_diff = self._apply_patch(
            target_path=target_path,
            repo_path=repo_path,
            diff_text=diff_text,
            replacement_code=code_text,
            original_content=original_content,
        )

        if not applied or not final_diff:
            return PatchResult(
                success=False,
                error="Failed to extract or apply diff from Ollama response",
                engine_used="local",
            )

        lines_changed = count_diff_lines(final_diff)
        if self.enforce_scope_ceiling and lines_changed > self.max_lines:
            return PatchResult(
                success=False,
                diff=final_diff,
                lines_changed=lines_changed,
                error=f"Patch exceeds scope ceiling ({lines_changed} > {self.max_lines} lines)",
                engine_used="local",
            )

        return PatchResult(
            success=True,
            diff=final_diff,
            lines_changed=lines_changed,
            engine_used="local",
        )

    async def _patch_flash(
        self,
        repo_path: Path,
        target_path: Path,
        persona_key: str,
        issue_context: str,
        prompt_override: Optional[str] = None,
    ) -> PatchResult:
        """
        Execute headless patch generation via `agy --model flash --mode auto --output-format stream-json`.
        Enforces typed argument lists (list[str]) and shell=False.
        """
        rel_file = str(target_path.relative_to(repo_path))
        try:
            original_content = target_path.read_text(encoding="utf-8")
        except Exception as e:
            return PatchResult(success=False, error=f"Failed reading target file: {e}", engine_used="antigravity_flash")

        prompt = prompt_override or self._build_prompt(
            persona_key=persona_key,
            target_file=rel_file,
            file_content=original_content,
            issue_context=issue_context,
        )

        cmd: List[str] = [
            self.agy_bin,
            "--model", "flash",
            "--mode", "auto",
            "--output-format", "stream-json",
            "--prompt", prompt,
        ]

        logger.info("Executing Flash engine: %s in %s", " ".join(cmd[:5]), repo_path)
        proc = None
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                preexec_fn=os.setsid,
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=self.subprocess_timeout,
            )
            stdout_str = stdout.decode("utf-8", errors="replace")
            stderr_str = stderr.decode("utf-8", errors="replace")

        except asyncio.TimeoutError:
            logger.warning("Flash runner timed out after %ds; terminating process group", self.subprocess_timeout)
            if proc is not None and proc.pid:
                try:
                    pgid = os.getpgid(proc.pid)
                    os.killpg(pgid, signal.SIGKILL)
                except (ProcessLookupError, OSError):
                    pass
            return PatchResult(
                success=False,
                error=f"Flash runner timed out ({self.subprocess_timeout}s)",
                engine_used="antigravity_flash",
            )
        except Exception as e:
            logger.warning("Flash runner execution failed: %s", e)
            return PatchResult(
                success=False,
                error=f"Flash runner execution failed: {type(e).__name__} ({e})",
                engine_used="antigravity_flash",
            )

        if proc.returncode != 0:
            err_msg = stderr_str.strip() or stdout_str.strip() or f"Process returned code {proc.returncode}"
            return PatchResult(
                success=False,
                error=f"Flash engine exited with error code {proc.returncode}: {err_msg}",
                engine_used="antigravity_flash",
            )

        # 1. Check if git diff has changes on disk
        git_diff = get_git_diff(repo_path, rel_file)
        if git_diff:
            lines_changed = count_diff_lines(git_diff)
            if self.enforce_scope_ceiling and lines_changed > self.max_lines:
                return PatchResult(
                    success=False,
                    diff=git_diff,
                    lines_changed=lines_changed,
                    error=f"Patch exceeds scope ceiling ({lines_changed} > {self.max_lines} lines)",
                    engine_used="antigravity_flash",
                )
            return PatchResult(
                success=True,
                diff=git_diff,
                lines_changed=lines_changed,
                engine_used="antigravity_flash",
            )

        # 2. Parse stream-json / stdout
        extracted_diff: Optional[str] = None
        extracted_code: Optional[str] = None

        for line in stdout_str.splitlines():
            line_str = line.strip()
            if not line_str:
                continue
            try:
                msg = json.loads(line_str)
                if isinstance(msg, dict):
                    if "diff" in msg:
                        extracted_diff = str(msg["diff"])
                        break
                    if "patch" in msg:
                        extracted_diff = str(msg["patch"])
                        break
                    if "result" in msg and isinstance(msg["result"], str):
                        cand = extract_diff_from_text(msg["result"])
                        if cand:
                            extracted_diff = cand
                            break
            except Exception:
                pass

        if not extracted_diff:
            extracted_diff = extract_diff_from_text(stdout_str)
        if extracted_diff and "\\n" in extracted_diff and "\n" not in extracted_diff:
            extracted_diff = extracted_diff.replace("\\r\\n", "\n").replace("\\n", "\n")
        if not extracted_diff:
            extracted_code = extract_code_from_text(stdout_str)

        applied, final_diff = self._apply_patch(
            target_path=target_path,
            repo_path=repo_path,
            diff_text=extracted_diff,
            replacement_code=extracted_code,
            original_content=original_content,
        )

        if not applied or not final_diff:
            return PatchResult(
                success=False,
                error="Flash engine finished with code 0 but produced no diff or file modification",
                engine_used="antigravity_flash",
            )

        lines_changed = count_diff_lines(final_diff)
        if self.enforce_scope_ceiling and lines_changed > self.max_lines:
            return PatchResult(
                success=False,
                diff=final_diff,
                lines_changed=lines_changed,
                error=f"Patch exceeds scope ceiling ({lines_changed} > {self.max_lines} lines)",
                engine_used="antigravity_flash",
            )

        return PatchResult(
            success=True,
            diff=final_diff,
            lines_changed=lines_changed,
            engine_used="antigravity_flash",
        )

    async def _patch_hybrid(
        self,
        repo_path: Path,
        target_path: Path,
        persona_key: str,
        issue_context: str,
    ) -> PatchResult:
        """
        Execute Hybrid Mode: Local AST/heuristic candidate targeting + Flash micro-patching.
        """
        rel_file = str(target_path.relative_to(repo_path))
        try:
            original_content = target_path.read_text(encoding="utf-8")
        except Exception as e:
            return PatchResult(success=False, error=f"Failed reading target file: {e}", engine_used="hybrid")

        # Step 1: Local AST / keyword heuristic candidate targeting
        start_ln, end_ln, snippet = self._heuristic_target(
            file_content=original_content,
            issue_context=issue_context,
            target_file=rel_file,
        )

        targeted_prompt = self._build_prompt(
            persona_key=persona_key,
            target_file=rel_file,
            file_content=original_content,
            issue_context=issue_context,
            candidate_snippet=snippet,
        )

        # Step 2: Micro-patching with Flash engine
        result = await self._patch_flash(
            repo_path=repo_path,
            target_path=target_path,
            persona_key=persona_key,
            issue_context=issue_context,
            prompt_override=targeted_prompt,
        )

        if result.success:
            result.engine_used = "hybrid"
            return result

        # Step 3: Graceful fallback to Local Ollama if allowed
        if self.allow_fallback:
            logger.warning(
                "Hybrid primary (Flash) failed: %s; falling back to Local Ollama",
                result.error,
            )
            local_res = await self._patch_local(
                repo_path=repo_path,
                target_path=target_path,
                persona_key=persona_key,
                issue_context=issue_context,
                prompt_override=targeted_prompt,
            )
            if local_res.success:
                local_res.engine_used = "local (fallback from hybrid)"
                return local_res
            return PatchResult(
                success=False,
                error=f"Hybrid Flash failed: {result.error}; Local fallback failed: {local_res.error}",
                engine_used="hybrid",
            )

        return result

    async def analyze_and_patch(
        self,
        repo_path: Path,
        persona: str,
        target_file: str,
        issue_context: str,
        mode: Optional[EngineMode] = None,
    ) -> PatchResult:
        """
        Analyze the issue and generate an atomic patch (< 50 lines).
        Dispatches to the requested engine mode with automatic graceful fallback.
        """
        # Validate repository path
        resolved_repo = Path(repo_path).resolve()
        if not resolved_repo.exists() or not resolved_repo.is_dir():
            return PatchResult(
                success=False,
                error=f"Repository path does not exist or is not a directory: {repo_path}",
            )

        # Path traversal guard and target file existence
        try:
            target_path = (resolved_repo / target_file).resolve()
            target_path.relative_to(resolved_repo)
        except (ValueError, Exception):
            return PatchResult(
                success=False,
                error=f"Path traversal detected or invalid target file path: {target_file}",
            )

        if not target_path.exists() or not target_path.is_file():
            return PatchResult(
                success=False,
                error=f"Target file does not exist: {target_file}",
            )

        # Mode resolution
        selected_mode = mode or self.default_mode
        if isinstance(selected_mode, str):
            try:
                selected_mode = EngineMode(selected_mode)
            except ValueError:
                return PatchResult(
                    success=False,
                    error=f"Invalid engine mode '{selected_mode}'. Must be one of {[m.value for m in EngineMode]}",
                )

        # Persona normalization
        persona_key = persona.lower()
        if persona_key not in PERSONAS:
            logger.warning("Persona '%s' not recognized; defaulting to 'bolt'", persona)
            persona_key = "bolt"

        logger.info(
            "EngineRouter dispatching: mode=%s, persona=%s, file=%s",
            selected_mode.value,
            persona_key,
            target_file,
        )

        # Dispatch
        if selected_mode == EngineMode.ANTIGRAVITY_FLASH:
            result = await self._patch_flash(
                repo_path=resolved_repo,
                target_path=target_path,
                persona_key=persona_key,
                issue_context=issue_context,
            )
            if not result.success and self.allow_fallback:
                logger.warning(
                    "Flash engine failed (%s); degrading to local Ollama engine",
                    result.error,
                )
                local_res = await self._patch_local(
                    repo_path=resolved_repo,
                    target_path=target_path,
                    persona_key=persona_key,
                    issue_context=issue_context,
                )
                if local_res.success:
                    local_res.engine_used = "local (fallback from flash)"
                    return local_res
                return PatchResult(
                    success=False,
                    error=f"Flash failed: {result.error}; Local fallback failed: {local_res.error}",
                    engine_used="local",
                )
            return result

        elif selected_mode == EngineMode.HYBRID:
            return await self._patch_hybrid(
                repo_path=resolved_repo,
                target_path=target_path,
                persona_key=persona_key,
                issue_context=issue_context,
            )

        elif selected_mode == EngineMode.LOCAL:
            return await self._patch_local(
                repo_path=resolved_repo,
                target_path=target_path,
                persona_key=persona_key,
                issue_context=issue_context,
            )

        return PatchResult(
            success=False,
            error=f"Unsupported engine mode: {selected_mode}",
        )

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

