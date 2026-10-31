# Graph Report - jules  (2026-10-31)

## Corpus Check
- 39 files · ~27,988 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 534 nodes · 914 edges · 43 communities (27 shown, 16 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 43 edges (avg confidence: 0.65)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2f6db52b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Jules Hub
- scanner.py
- test_engine_router.py
- CDPBridge
- test_api.py
- Jules AI Agent - Lessons Learned & Behavioral Memory
- curator.py
- App.tsx
- WorktreeManager
- devDependencies
- test_scanner.py
- CDPResponse
- Workspace Agent Router — Jules Curator Hub
- create_app
- app.py
- compilerOptions
- Contributing to Jules MCP Server
- TaskLogManager
- Tasks
- Specifica Architetturale: Jules Hub (Autonomous Junior Coder & Antigravity Escalation Pipeline)
- mock_worktree_manager
- compilerOptions
- bolt.md
- palette.md
- sentinel.md
- worktree_manager.py
- Suggestion
- __init__.py
- test_api_projects
- test_api_suggestions_default
- test_api_suggestions_with_filters
- test_api_escalate_port_closed_resilience
- test_api_run_success_flow
- test_api_run_test_failure_escalation
- test_api_run_background
- test_api_stream_logs
- test_api_stream_not_found
- test_cors_middleware
- test_api_health
- jules-hub

## God Nodes (most connected - your core abstractions)
1. `EngineRouter` - 30 edges
2. `CDPBridge` - 26 edges
3. `TaskLogManager` - 24 edges
4. `WorktreeManager` - 23 edges
5. `compilerOptions` - 16 edges
6. `WorktreeContext` - 14 edges
7. `main()` - 13 edges
8. `create_app()` - 13 edges
9. `CDPResponse` - 12 edges
10. `Suggestion` - 12 edges

## Surprising Connections (you probably didn't know these)
- `client()` --calls--> `create_app()`  [EXTRACTED]
  tests/test_api.py → hub/app.py
- `mock_cdp_bridge()` --calls--> `CDPResponse`  [EXTRACTED]
  tests/test_api.py → hub/cdp_bridge.py
- `test_api_escalate_port_closed_resilience()` --calls--> `CDPResponse`  [EXTRACTED]
  tests/test_api.py → hub/cdp_bridge.py
- `test_count_diff_lines()` --calls--> `count_diff_lines()`  [EXTRACTED]
  tests/test_engine_router.py → hub/engine_router.py
- `test_count_diff_lines_escaped_newlines()` --calls--> `count_diff_lines()`  [EXTRACTED]
  tests/test_engine_router.py → hub/engine_router.py

## Import Cycles
- None detected.

## Communities (43 total, 16 thin omitted)

### Community 0 - "Jules Hub"
Cohesion: 0.20
Nodes (9): Architecture and Core Components, CLI Entry Point, Hub Components, Jules Hub, License, Local Development and Testing, Overview, Quickstart and Docker Deployment (+1 more)

### Community 1 - "scanner.py"
Cohesion: 0.25
Nodes (10): fetch_ci_failure_log(), get_failing_pr(), Any, CompletedProcess, Path, Jules Hub Scanner: Repository inspection and issue suggestion engine. Extracts…, Run a subprocess command safely without shell redirection. Enforces typed…, Fetch PR details and checks status using GitHub CLI ('gh'). Uses list[str]… (+2 more)

### Community 2 - "test_engine_router.py"
Cohesion: 0.06
Nodes (58): EngineMode, apply_hunks_to_content(), count_diff_lines(), EngineRouter, extract_code_from_text(), extract_diff_from_text(), get_git_diff(), Path (+50 more)

### Community 3 - "CDPBridge"
Cohesion: 0.09
Nodes (36): EscalateRequest, CDPBridge, Bridge to Antigravity Desktop via Chrome DevTools Protocol (CDP). Default…, Query http://{cdp_host}:{cdp_port}/json/list to find the target…, Escalate a worktree review request to Antigravity Desktop via CDP…, patch, asyncio, fixture (+28 more)

### Community 4 - "test_api.py"
Cohesion: 0.17
Nodes (11): Unit tests for Jules Hub FastAPI Server (hub/app.py). Tests REST endpoints…, Verify /api/worktrees returns active worktree sessions., Verify /api/worktrees/prune prunes all worktrees when no path is provided., Verify /api/worktrees/prune prunes a specific worktree path., Verify /api/escalate invokes CDPBridge and returns 200., Verify /api/run in dry_run mode completes immediately., test_api_escalate_success(), test_api_run_dry_run() (+3 more)

### Community 5 - "Jules AI Agent - Lessons Learned & Behavioral Memory"
Cohesion: 0.22
Nodes (8): 1. Jules MCP Native Tool & Single Worker Standard, 2. Infrastruttura Docker Remota & Mappa di Topologia, 3. Gestione Obbligatoria Dual-Phase (Session & PR Management) e Resilienza Errori MCP, 4. Cancellazione Immediata dei Branch Remote & Local dopo il Merge PR, 5. Defensive Timeout and Error Handling in Jules MCP, 6. Mandatory Pre-Compiled Container Images Policy (GHCR), 7. Preference for Stateless HTTP (/rpc) and Stdio Transports Over SSE, Jules AI Agent - Lessons Learned & Behavioral Memory

### Community 6 - "curator.py"
Cohesion: 0.09
Nodes (38): ArgumentParser, build_parser(), cleanup_all_worktrees(), detect_test_command(), fetch_ci_failure_log(), find_suggestions(), get_failing_pr(), list_registered_repos() (+30 more)

### Community 7 - "App.tsx"
Cohesion: 0.10
Nodes (32): api, ApiError, useTaskLogs(), App(), DiffDrawer(), DiffDrawerProps, RepoSelector(), RepoSelectorProps (+24 more)

### Community 8 - "WorktreeManager"
Cohesion: 0.05
Nodes (51): detect_test_command(), Any, CompletedProcess, Path, Execute tests asynchronously inside a worktree with a process group kill…, Context manager for an isolated git worktree. Supports both synchronous…, Mark session as aborted and clean up immediately., Mark session as successfully completed. (+43 more)

### Community 9 - "devDependencies"
Cohesion: 0.06
Nodes (32): autoprefixer, lucide-react, postcss, react, react-dom, tailwindcss, @types/react, @types/react-dom (+24 more)

### Community 10 - "test_scanner.py"
Cohesion: 0.15
Nodes (19): find_suggestions(), Scan repository for concrete micro-improvements across Bolt, Palette, or…, Suggestion, Path, Unit tests for Jules Hub Scanner (hub/scanner.py). Verifies detection of micro-…, Verify Bolt detects performance bottlenecks., Verify mode and category filters correctly partition results., Verify get_failing_pr handles gh checks and failing checks correctly. (+11 more)

### Community 11 - "CDPResponse"
Cohesion: 0.28
Nodes (8): BaseCDPResponse, CDPResponse, Antigravity Chrome DevTools Protocol (CDP) Escalation Bridge. Connects to…, CDP response with explicit error field support., CDPResponse, EscalateRequest, Response from Antigravity Chrome DevTools Protocol bridge., Request payload to escalate a worktree to Antigravity Senior Review via CDP.

### Community 12 - "Workspace Agent Router — Jules Curator Hub"
Cohesion: 0.40
Nodes (4): 📖 [ALL AGENTS] Repository Documentation Index, 🛡️ [ALL AGENTS] Worktree Isolation & Safety Directives, 🛠️ [MASTER AGENT ONLY] Curator CLI Reference, Workspace Agent Router — Jules Curator Hub

### Community 13 - "create_app"
Cohesion: 0.25
Nodes (8): FastAPI, create_app(), Path, Create and configure the Jules Hub FastAPI application., Verify GET / returns JSON status when UI is not built., Verify GET / serves index.html and SPA fallback when ui/dist exists., test_conditional_ui_mount_built(), test_conditional_ui_mount_not_built()

### Community 14 - "app.py"
Cohesion: 0.13
Nodes (23): BaseModel, Enum, Jules Hub FastAPI Server. Provides REST and SSE endpoints for worktree…, EngineMode, EscalateResponse, PatchResult, PersonaConfig, ProjectInfo (+15 more)

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

### Community 20 - "mock_worktree_manager"
Cohesion: 0.33
Nodes (6): client(), mock_cdp_bridge(), mock_engine_router(), mock_worktree_manager(), fixture, Path

### Community 21 - "compilerOptions"
Cohesion: 0.22
Nodes (8): vite.config.ts, compilerOptions, allowSyntheticDefaultImports, composite, module, moduleResolution, skipLibCheck, include

### Community 25 - "worktree_manager.py"
Cohesion: 0.33
Nodes (5): Metadata describing an isolated git worktree session., WorktreeSessionInfo, cleanup_all(), Jules Hub Worktree Manager: Isolated git worktree lifecycle and test execution.…, Module-level cleanup helper.

### Community 26 - "Suggestion"
Cohesion: 0.33
Nodes (5): Any, A single micro-improvement suggestion generated by the scanner., Allow dict-like get access for backward compatibility., Allow dict-like subscription access., Suggestion

## Knowledge Gaps
- **81 isolated node(s):** `jules-hub`, `name`, `private`, `version`, `type` (+76 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **16 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `EngineRouter` connect `test_engine_router.py` to `TaskLogManager`, `test_api.py`, `create_app`, `app.py`?**
  _High betweenness centrality (0.068) - this node is a cross-community bridge._
- **Why does `WorktreeManager` connect `WorktreeManager` to `test_api.py`, `create_app`, `app.py`, `TaskLogManager`, `worktree_manager.py`?**
  _High betweenness centrality (0.060) - this node is a cross-community bridge._
- **Why does `CDPBridge` connect `CDPBridge` to `test_api.py`, `CDPResponse`, `create_app`, `app.py`, `TaskLogManager`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `EngineRouter` (e.g. with `TaskLogManager` and `EngineMode`) actually correct?**
  _`EngineRouter` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `CDPBridge` (e.g. with `TaskLogManager` and `CDPResponse`) actually correct?**
  _`CDPBridge` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 22 inferred relationships involving `patch` (e.g. with `test_api_suggestions_default()` and `test_api_suggestions_with_filters()`) actually correct?**
  _`patch` has 22 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `TaskLogManager` (e.g. with `CDPBridge` and `CDPResponse`) actually correct?**
  _`TaskLogManager` has 13 INFERRED edges - model-reasoned connections that need verification._