# Workspace Agent Router — Julius Curator Hub

> **Julius Curator Hub** is an autonomous, background worktree runner and code polishing engine.
> It implements autonomous personas for code curation:
> - **⚡ Bolt**: Performance & efficiency optimizer.
> - **🎨 Palette**: Micro-UX & accessibility craftsperson.
> - **🛡️ Sentinel**: Security, hardening & defense-in-depth guardian.

## 📖 [ALL AGENTS] Repository Documentation Index
Before starting any work, consult the project documentation:

- **Global Agent Guidelines & Safety:** Refer to `~/.gemini/config/AGENTS.md` for shell rules and execution protocols.
- **Curator Runner:** Inspect [curator.py](file:///home/federico/jules/curator.py) for the CLI entry point and worktree isolation lifecycle.
- **Journals (Critical Learnings Only):**
  - Performance: [journal/bolt.md](file:///home/federico/jules/journal/bolt.md)
  - Micro-UX & a11y: [journal/palette.md](file:///home/federico/jules/journal/palette.md)
  - Security & Hardening: [journal/sentinel.md](file:///home/federico/jules/journal/sentinel.md)
- **Lessons Learned & Past Bugs:** Read [.agents/memory/lessons.md](file:///home/federico/jules/.agents/memory/lessons.md).

## 🛡️ [ALL AGENTS] Worktree Isolation & Safety Directives
- **Zero Dirty Working Tree Guarantee:** Never modify files directly inside the primary working directories of target projects (`/home/federico/RoosterLab`, `/home/federico/ag2r`, etc.). All exploratory scans, optimizations, and test runs MUST occur inside dedicated isolated worktrees (`/home/federico/jules/worktrees/<project>-<mode>`).
- **Hard Scope Ceiling (< 50 Lines):** Every automated intervention must be strictly smaller than 50 lines. Large refactors or architectural overhauls are forbidden.
- **Zero-Noise Fallback:** If no clear, measurable win or fix is found, abort cleanly. Do not create empty diffs or micro-optimizations of cold paths.
- **Automated Test Gate:** Modifications must never be committed without running the target project's automated test suite inside the worktree (`./run_fast_tests.sh`, `npx tsc`, `pytest`).

## 🛠️ [MASTER AGENT ONLY] Curator CLI Reference
Invoke the curator via:
```bash
# Run a specific persona on a registered project:
python3 /home/federico/jules/curator.py run --repo RoosterLab --mode bolt
python3 /home/federico/jules/curator.py run --repo ag2r --mode palette
python3 /home/federico/jules/curator.py run --repo SupervisOwl --mode sentinel

# CI Auto-Fixer:
python3 /home/federico/jules/curator.py fix-ci --repo RoosterLab --pr 42

# Knowledge & Utilities:
python3 /home/federico/jules/curator.py knowledge --repo RoosterLab --mode bolt
python3 /home/federico/jules/curator.py list      # Show all registered target projects
python3 /home/federico/jules/curator.py status    # Show active worktrees
python3 /home/federico/jules/curator.py cleanup   # Prune and remove stale worktrees
```
