# Graph Report - jules  (2026-10-31)

## Corpus Check
- 12 files · ~8,799 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 124 nodes · 204 edges · 25 communities (17 shown, 8 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `48e433e4`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Jules MCP Server
- jules_mcp.py
- tool
- CatchAllMessagesFallbackMiddleware
- direct_rpc_handler
- Jules AI Agent - Lessons Learned & Behavioral Memory
- test_curator.py
- Any
- main
- _make_api_request
- Path
- jules-mcp-server
- Workspace Agent Router — Jules Curator Hub
- run_cmd
- curator.py
- find_suggestions
- Contributing to Jules MCP Server
- cleanup_all_worktrees
- delete_session
- list_all_activities
- load_knowledge
- bolt.md
- palette.md
- sentinel.md

## God Nodes (most connected - your core abstractions)
1. `_make_api_request()` - 16 edges
2. `main()` - 13 edges
3. `run_cmd()` - 10 edges
4. `_clean_session_id()` - 9 edges
5. `Jules AI Agent - Lessons Learned & Behavioral Memory` - 8 edges
6. `_get_pagination_params()` - 7 edges
7. `list_sessions()` - 7 edges
8. `list_activities()` - 7 edges
9. `list_all_activities()` - 7 edges
10. `find_suggestions()` - 7 edges

## Surprising Connections (you probably didn't know these)
- `_run_category_filter_checks()` --calls--> `find_suggestions()`  [EXTRACTED]
  tests/test_curator.py → curator.py
- `test_suggest_parser_arguments()` --calls--> `build_parser()`  [EXTRACTED]
  tests/test_curator.py → curator.py

## Import Cycles
- None detected.

## Communities (25 total, 8 thin omitted)

### Community 0 - "Jules MCP Server"
Cohesion: 0.14
Nodes (13): 1. Docker Compose (Recommended Production Setup), 2. Standalone Docker Run, 🔌 Client Integration Guide (`mcp_config.json`), Jules MCP Server, Key Features, 📄 License, 🛠️ Local Development & Testing, 🛠️ MCP Tools Reference (+5 more)

### Community 1 - "jules_mcp.py"
Cohesion: 0.25
Nodes (10): approve_session_plan(), _clean_session_id(), get_headers(), get_session(), get_source(), Get details for a single session by ID or resource name., Approve the generated plan for a session in a single native MCP call., Send a user message (prompt) to an existing session. (+2 more)

### Community 2 - "tool"
Cohesion: 0.50
Nodes (5): clean_completed_sessions(), list_sessions(), List sessions with optional automatic pagination to retrieve sessions natively., Scans all sessions and deletes completed, terminated, failed, or inactive…, tool

### Community 3 - "CatchAllMessagesFallbackMiddleware"
Cohesion: 0.50
Nodes (3): CatchAllMessagesFallbackMiddleware, Middleware to catch POST requests on /messages or /messages/ (even with…, BaseHTTPMiddleware

### Community 5 - "Jules AI Agent - Lessons Learned & Behavioral Memory"
Cohesion: 0.22
Nodes (8): 1. Jules MCP Native Tool & Single Worker Standard, 2. Infrastruttura Docker Remota & Mappa di Topologia, 3. Gestione Obbligatoria Dual-Phase (Session & PR Management) e Resilienza Errori MCP, 4. Cancellazione Immediata dei Branch Remote & Local dopo il Merge PR, 5. Defensive Timeout and Error Handling in Jules MCP, 6. Mandatory Pre-Compiled Container Images Policy (GHCR), 7. Preference for Stateless HTTP (/rpc) and Stdio Transports Over SSE, Jules AI Agent - Lessons Learned & Behavioral Memory

### Community 6 - "test_curator.py"
Cohesion: 0.28
Nodes (8): Path, Unit tests for Jules Curator Hub (curator.py) Validating suggest category…, Verifica con dati temporanei che find_suggestions assegni correttamente il…, Verifica che l'argparser del comando 'suggest' accetti: - --category, -c con…, Core assertion logic for find_suggestions category filter and tags., _run_category_filter_checks(), test_find_suggestions_category_filter(), test_suggest_parser_arguments()

### Community 7 - "Any"
Cohesion: 0.36
Nodes (8): get_all_sources(), _get_pagination_params(), list_activities(), list_sources(), Any, List activities for a specific session., List sources with optional filter and pagination., Get all sources with optional filtering (auto-pagination).

### Community 8 - "main"
Cohesion: 0.29
Nodes (7): ArgumentParser, build_parser(), main(), Record a new critical learning into both the repo's .jules/<mode>.md and the…, Resolve project name or path against projects_registry.json or direct path., record_learning(), resolve_project_path()

### Community 9 - "_make_api_request"
Cohesion: 0.33
Nodes (6): create_session(), get_activity(), _make_api_request(), Helper function to make API requests with rigid hard timeouts., Create a new Jules session for a given source and prompt., Get details for a single activity by ID.

### Community 10 - "Path"
Cohesion: 0.40
Nodes (3): Path, Context manager handling creation and cleanup of isolated git worktrees., WorktreeSession

### Community 12 - "Workspace Agent Router — Jules Curator Hub"
Cohesion: 0.40
Nodes (4): 📖 [ALL AGENTS] Repository Documentation Index, 🛡️ [ALL AGENTS] Worktree Isolation & Safety Directives, 🛠️ [MASTER AGENT ONLY] Curator CLI Reference, Workspace Agent Router — Jules Curator Hub

### Community 13 - "run_cmd"
Cohesion: 0.40
Nodes (5): CompletedProcess, fetch_ci_failure_log(), Run a shell command safely without shell redirection., Fetch failing CI logs for a branch, offloading to local LLM on RTX 5070 Ti if >…, run_cmd()

### Community 14 - "curator.py"
Cohesion: 0.50
Nodes (4): detect_test_command(), Autodetect the fastest local test command for the repository., Execute tests in worktree and return success status and output., run_tests_in_worktree()

### Community 15 - "find_suggestions"
Cohesion: 0.40
Nodes (5): find_suggestions(), get_failing_pr(), Any, Fetch PR details and checks status using GitHub CLI., Scan repository for concrete micro-improvements across Bolt, Palette, or…

### Community 16 - "Contributing to Jules MCP Server"
Cohesion: 0.50
Nodes (3): Contributing to Jules MCP Server, Development Setup, Pull Request Guidelines

### Community 17 - "cleanup_all_worktrees"
Cohesion: 0.50
Nodes (4): cleanup_all_worktrees(), list_registered_repos(), Return all valid git repositories registered in projects_registry.json., Prune and remove all worktrees managed by Jules.

## Knowledge Gaps
- **26 isolated node(s):** `jules-mcp-server`, `📖 [ALL AGENTS] Repository Documentation Index`, `🛡️ [ALL AGENTS] Worktree Isolation & Safety Directives`, `🛠️ [MASTER AGENT ONLY] Curator CLI Reference`, `1. Jules MCP Native Tool & Single Worker Standard` (+21 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `main` to `Path`, `run_cmd`, `curator.py`, `find_suggestions`, `cleanup_all_worktrees`, `load_knowledge`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **Why does `find_suggestions()` connect `find_suggestions` to `main`, `Path`, `curator.py`, `test_curator.py`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **Why does `CatchAllMessagesFallbackMiddleware` connect `CatchAllMessagesFallbackMiddleware` to `jules_mcp.py`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **What connects `jules-mcp-server`, `📖 [ALL AGENTS] Repository Documentation Index`, `🛡️ [ALL AGENTS] Worktree Isolation & Safety Directives` to the rest of the system?**
  _26 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Jules MCP Server` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._