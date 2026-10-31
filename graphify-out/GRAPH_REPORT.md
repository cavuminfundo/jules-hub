# Graph Report - jules  (2026-10-31)

## Corpus Check
- 41 files · ~30,481 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 580 nodes · 1011 edges · 31 communities (26 shown, 5 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 43 edges (avg confidence: 0.65)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `48e433e4`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Jules MCP Server
- jules_mcp.py
- test_engine_router.py
- CDPBridge
- test_api.py
- Jules AI Agent - Lessons Learned & Behavioral Memory
- curator.py
- App.tsx
- WorktreeContext
- devDependencies
- test_scanner.py
- jules-mcp-server
- Workspace Agent Router — Jules Curator Hub
- WorktreeManager
- app.py
- compilerOptions
- Contributing to Jules MCP Server
- TaskLogManager
- Tasks
- Specifica Architetturale: Jules Hub (Autonomous Junior Coder & Antigravity Escalation Pipeline)
- compilerOptions
- bolt.md
- palette.md
- sentinel.md
- worktree_manager.py
- .get
- __init__.py

## God Nodes (most connected - your core abstractions)
1. `EngineRouter` - 30 edges
2. `CDPBridge` - 26 edges
3. `TaskLogManager` - 24 edges
4. `WorktreeManager` - 23 edges
5. `_make_api_request()` - 16 edges
6. `compilerOptions` - 16 edges
7. `WorktreeContext` - 14 edges
8. `main()` - 13 edges
9. `create_app()` - 13 edges
10. `CDPResponse` - 12 edges

## Surprising Connections (you probably didn't know these)
- `client()` --calls--> `create_app()`  [EXTRACTED]
  tests/test_api.py → hub/app.py
- `test_conditional_ui_mount_built()` --calls--> `create_app()`  [EXTRACTED]
  tests/test_api.py → hub/app.py
- `test_conditional_ui_mount_not_built()` --calls--> `create_app()`  [EXTRACTED]
  tests/test_api.py → hub/app.py
- `mock_cdp_bridge()` --calls--> `CDPResponse`  [EXTRACTED]
  tests/test_api.py → hub/cdp_bridge.py
- `test_api_escalate_port_closed_resilience()` --calls--> `CDPResponse`  [EXTRACTED]
  tests/test_api.py → hub/cdp_bridge.py

## Import Cycles
- None detected.

## Communities (31 total, 5 thin omitted)

### Community 0 - "Jules MCP Server"
Cohesion: 0.14
Nodes (13): 1. Docker Compose (Recommended Production Setup), 2. Standalone Docker Run, 🔌 Client Integration Guide (`mcp_config.json`), Jules MCP Server, Key Features, 📄 License, 🛠️ Local Development & Testing, 🛠️ MCP Tools Reference (+5 more)

### Community 1 - "jules_mcp.py"
Cohesion: 0.12
Nodes (38): approve_session_plan(), CatchAllMessagesFallbackMiddleware, clean_completed_sessions(), _clean_session_id(), create_session(), delete_session(), direct_rpc_handler(), get_activity() (+30 more)

### Community 2 - "test_engine_router.py"
Cohesion: 0.06
Nodes (58): EngineMode, apply_hunks_to_content(), count_diff_lines(), EngineRouter, extract_code_from_text(), extract_diff_from_text(), get_git_diff(), Path (+50 more)

### Community 3 - "CDPBridge"
Cohesion: 0.08
Nodes (44): BaseCDPResponse, EscalateRequest, CDPBridge, CDPResponse, Antigravity Chrome DevTools Protocol (CDP) Escalation Bridge. Connects to…, CDP response with explicit error field support., Bridge to Antigravity Desktop via Chrome DevTools Protocol (CDP). Default…, Query http://{cdp_host}:{cdp_port}/json/list to find the target… (+36 more)

### Community 4 - "test_api.py"
Cohesion: 0.05
Nodes (45): PatchResult, Result of an engine patch attempt (< 50 lines)., client(), mock_cdp_bridge(), mock_engine_router(), mock_worktree_manager(), fixture, Path (+37 more)

### Community 5 - "Jules AI Agent - Lessons Learned & Behavioral Memory"
Cohesion: 0.22
Nodes (8): 1. Jules MCP Native Tool & Single Worker Standard, 2. Infrastruttura Docker Remota & Mappa di Topologia, 3. Gestione Obbligatoria Dual-Phase (Session & PR Management) e Resilienza Errori MCP, 4. Cancellazione Immediata dei Branch Remote & Local dopo il Merge PR, 5. Defensive Timeout and Error Handling in Jules MCP, 6. Mandatory Pre-Compiled Container Images Policy (GHCR), 7. Preference for Stateless HTTP (/rpc) and Stdio Transports Over SSE, Jules AI Agent - Lessons Learned & Behavioral Memory

### Community 6 - "curator.py"
Cohesion: 0.09
Nodes (38): ArgumentParser, build_parser(), cleanup_all_worktrees(), detect_test_command(), fetch_ci_failure_log(), find_suggestions(), get_failing_pr(), list_registered_repos() (+30 more)

### Community 7 - "App.tsx"
Cohesion: 0.10
Nodes (32): api, ApiError, useTaskLogs(), App(), DiffDrawer(), DiffDrawerProps, RepoSelector(), RepoSelectorProps (+24 more)

### Community 8 - "WorktreeContext"
Cohesion: 0.08
Nodes (18): Any, CompletedProcess, Path, Context manager for an isolated git worktree. Supports both synchronous…, Mark session as aborted and clean up immediately., Mark session as successfully completed., Forcefully remove worktree and prune dangling locks., Allow tuple unpacking: (worktree_path, branch) = ctx. (+10 more)

### Community 9 - "devDependencies"
Cohesion: 0.06
Nodes (32): autoprefixer, lucide-react, postcss, react, react-dom, tailwindcss, @types/react, @types/react-dom (+24 more)

### Community 10 - "test_scanner.py"
Cohesion: 0.10
Nodes (31): A single micro-improvement suggestion generated by the scanner., Suggestion, fetch_ci_failure_log(), find_suggestions(), get_failing_pr(), Any, CompletedProcess, Path (+23 more)

### Community 12 - "Workspace Agent Router — Jules Curator Hub"
Cohesion: 0.40
Nodes (4): 📖 [ALL AGENTS] Repository Documentation Index, 🛡️ [ALL AGENTS] Worktree Isolation & Safety Directives, 🛠️ [MASTER AGENT ONLY] Curator CLI Reference, Workspace Agent Router — Jules Curator Hub

### Community 13 - "WorktreeManager"
Cohesion: 0.12
Nodes (31): detect_test_command(), Manages isolated git worktrees across registered repositories. Supports…, Delegate to run_tests_async helper., Autodetect the fastest local test command for the repository. 1. Custom repo…, WorktreeManager, MonkeyPatch, _init_dummy_git_repo(), asyncio (+23 more)

### Community 14 - "app.py"
Cohesion: 0.11
Nodes (27): BaseModel, Enum, FastAPI, create_app(), Path, Jules Hub FastAPI Server. Provides REST and SSE endpoints for worktree…, Create and configure the Jules Hub FastAPI application., EngineMode (+19 more)

### Community 15 - "compilerOptions"
Cohesion: 0.09
Nodes (22): DOM, DOM.Iterable, ES2020, src, compilerOptions, allowImportingTsExtensions, isolatedModules, jsx (+14 more)

### Community 16 - "Contributing to Jules MCP Server"
Cohesion: 0.50
Nodes (3): Contributing to Jules MCP Server, Development Setup, Pull Request Guidelines

### Community 17 - "TaskLogManager"
Cohesion: 0.14
Nodes (9): execute_run_task(), Any, In-memory event hub for task log streaming via SSE., Executes patch generation and test validation inside an isolated worktree., TaskLogManager, Queue, RunRequest, RunResponse (+1 more)

### Community 18 - "Tasks"
Cohesion: 0.18
Nodes (10): Automatic Multi-Domain Audit Matrix (Stage 1 & Stage 2), Domain Skills & Sub-Agent Roster (N-Domain Mapping), Global Constraints, Jules Hub Implementation Plan (Junior/Senior Coder Pipeline), Task 1: Backend Core — Packaging, Data Models, Scanner & WorktreeManager, Task 2: Backend — Multi-Engine Router (Flash, Local Ollama, Hybrid), Task 3: Backend — CDP Escalation Bridge, SSE Streaming & FastAPI Server, Task 4: Frontend — Web Cockpit Dashboard (React + Tailwind Dark UI) (+2 more)

### Community 19 - "Specifica Architetturale: Jules Hub (Autonomous Junior Coder & Antigravity Escalation Pipeline)"
Cohesion: 0.20
Nodes (9): 1. Visione di Prodotto & Modello Organizzativo (Junior/Senior Coder), 2. Modalità di Calcolo & Quota Shield (3 Engine Mode), 3. Architettura Tecnica del Backend (`jules-hub`), 4. Interfaccia Web Dashboard (UI/UX), 5. Strategia di Packaging e Deploy (Dockge & GHCR), 6. Piano di Implementazione & Passi Successivi, Componenti Chiave del Backend:, Il Pattern Organizzativo "Junior / Senior Developer" (+1 more)

### Community 21 - "compilerOptions"
Cohesion: 0.22
Nodes (8): vite.config.ts, compilerOptions, allowSyntheticDefaultImports, composite, module, moduleResolution, skipLibCheck, include

### Community 25 - "worktree_manager.py"
Cohesion: 0.33
Nodes (5): cleanup_all(), Jules Hub Worktree Manager: Isolated git worktree lifecycle and test execution.…, Execute tests asynchronously inside a worktree with a process group kill…, Module-level cleanup helper., run_tests_async()

### Community 26 - ".get"
Cohesion: 0.40
Nodes (3): Any, Allow dict-like get access for backward compatibility., Allow dict-like subscription access.

## Knowledge Gaps
- **84 isolated node(s):** `jules-mcp-server`, `name`, `private`, `version`, `type` (+79 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `EngineRouter` connect `test_engine_router.py` to `TaskLogManager`, `test_api.py`, `app.py`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Why does `WorktreeManager` connect `WorktreeManager` to `test_api.py`, `WorktreeContext`, `app.py`, `TaskLogManager`, `worktree_manager.py`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `CDPBridge` connect `CDPBridge` to `TaskLogManager`, `test_api.py`, `app.py`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `EngineRouter` (e.g. with `TaskLogManager` and `EngineMode`) actually correct?**
  _`EngineRouter` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `CDPBridge` (e.g. with `TaskLogManager` and `CDPResponse`) actually correct?**
  _`CDPBridge` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 22 inferred relationships involving `patch` (e.g. with `test_api_suggestions_default()` and `test_api_suggestions_with_filters()`) actually correct?**
  _`patch` has 22 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `TaskLogManager` (e.g. with `CDPBridge` and `CDPResponse`) actually correct?**
  _`TaskLogManager` has 13 INFERRED edges - model-reasoned connections that need verification._