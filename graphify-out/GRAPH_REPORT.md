# Graph Report - jules  (2026-10-31)

## Corpus Check
- 48 files · ~42,373 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 679 nodes · 1233 edges · 42 communities (37 shown, 5 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 59 edges (avg confidence: 0.62)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2f6db52b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Jules Hub
- ConfigStore
- EngineRouter
- CDPBridge
- test_api.py
- Jules AI Agent - Lessons Learned & Behavioral Memory
- curator.py
- types.ts
- test_worktree_manager.py
- devDependencies
- find_suggestions
- CDPResponse
- Workspace Agent Router — Jules Curator Hub
- create_app
- models.py
- compilerOptions
- Contributing to Jules MCP Server
- execute_run_task
- Tasks
- Specifica Architetturale: Jules Hub (Autonomous Junior Coder & Antigravity Escalation Pipeline)
- Specifiche Tecniche di Jules Hub v2 - Autonomia del Cockpit
- compilerOptions
- bolt.md
- palette.md
- sentinel.md
- worktree_manager.py
- .get
- __init__.py
- WorktreeManager
- Jules Hub v2 — Autonomous Cockpit Implementation Plan
- BaseModel
- WorktreeContext
- probe_ollama_instance
- BackgroundScheduler
- ._loop
- run_cmd
- TaskLogManager
- test_env_vars_override
- jules-hub

## God Nodes (most connected - your core abstractions)
1. `EngineRouter` - 35 edges
2. `ConfigStore` - 32 edges
3. `CDPBridge` - 31 edges
4. `TaskLogManager` - 30 edges
5. `WorktreeManager` - 23 edges
6. `create_app()` - 22 edges
7. `BackgroundScheduler` - 17 edges
8. `compilerOptions` - 16 edges
9. `CDPResponse` - 14 edges
10. `EscalateRequest` - 14 edges

## Surprising Connections (you probably didn't know these)
- `client()` --calls--> `create_app()`  [EXTRACTED]
  tests/test_api.py → hub/app.py
- `mock_cdp_bridge()` --calls--> `CDPResponse`  [EXTRACTED]
  tests/test_api.py → hub/cdp_bridge.py
- `test_cdp_model_picker_and_escalate_offline()` --calls--> `CDPBridge`  [EXTRACTED]
  tests/test_scheduler_and_senior.py → hub/cdp_bridge.py
- `test_api_config_routes()` --calls--> `ConfigStore`  [EXTRACTED]
  tests/test_scheduler_and_senior.py → hub/config_store.py
- `test_api_ollama_and_cdp_routes()` --calls--> `ConfigStore`  [EXTRACTED]
  tests/test_scheduler_and_senior.py → hub/config_store.py

## Import Cycles
- None detected.

## Communities (42 total, 5 thin omitted)

### Community 0 - "Jules Hub"
Cohesion: 0.20
Nodes (9): Architecture and Core Components, CLI Entry Point, Hub Components, Jules Hub, License, Local Development and Testing, Overview, Quickstart and Docker Deployment (+1 more)

### Community 1 - "ConfigStore"
Cohesion: 0.18
Nodes (12): ConfigStore, Path, SeniorReviewResult, Atomic JSON store for HubConfig and HubState using pathlib.Path and file rename., HubState, Runtime state persisted to data/hub_state.json., HubConfig, Path (+4 more)

### Community 2 - "EngineRouter"
Cohesion: 0.06
Nodes (60): EngineMode, apply_hunks_to_content(), count_diff_lines(), EngineRouter, extract_code_from_text(), extract_diff_from_text(), get_git_diff(), Path (+52 more)

### Community 3 - "CDPBridge"
Cohesion: 0.07
Nodes (42): EscalateRequest, CDPBridge, Escalate a worktree review request to Antigravity Desktop via CDP…, Query Antigravity Model Picker via CDP Runtime.evaluate or return default…, Select senior model in Antigravity DOM and trigger Senior Review via CDP…, Bridge to Antigravity Desktop via Chrome DevTools Protocol (CDP). Default…, Query http://{cdp_host}:{cdp_port}/json/list to find the target…, patch (+34 more)

### Community 4 - "test_api.py"
Cohesion: 0.06
Nodes (39): PatchResult, Result of an engine patch attempt (< 50 lines)., Metadata describing an isolated git worktree session., WorktreeSessionInfo, client(), mock_cdp_bridge(), mock_engine_router(), mock_worktree_manager() (+31 more)

### Community 5 - "Jules AI Agent - Lessons Learned & Behavioral Memory"
Cohesion: 0.22
Nodes (8): 1. Jules MCP Native Tool & Single Worker Standard, 2. Infrastruttura Docker Remota & Mappa di Topologia, 3. Gestione Obbligatoria Dual-Phase (Session & PR Management) e Resilienza Errori MCP, 4. Cancellazione Immediata dei Branch Remote & Local dopo il Merge PR, 5. Defensive Timeout and Error Handling in Jules MCP, 6. Mandatory Pre-Compiled Container Images Policy (GHCR), 7. Preference for Stateless HTTP (/rpc) and Stdio Transports Over SSE, Jules AI Agent - Lessons Learned & Behavioral Memory

### Community 6 - "curator.py"
Cohesion: 0.09
Nodes (38): ArgumentParser, build_parser(), cleanup_all_worktrees(), detect_test_command(), fetch_ci_failure_log(), find_suggestions(), get_failing_pr(), list_registered_repos() (+30 more)

### Community 7 - "types.ts"
Cohesion: 0.08
Nodes (45): api, ApiError, useTaskLogs(), App(), DiffDrawer(), DiffDrawerProps, RepoSelector(), RepoSelectorProps (+37 more)

### Community 8 - "test_worktree_manager.py"
Cohesion: 0.15
Nodes (22): Delegate to run_tests_async helper., _init_dummy_git_repo(), asyncio, Path, Unit tests for Jules Hub Worktree Manager (hub/worktree_manager.py). Tests…, Verify that an exception inside WorktreeContext triggers auto-prune cleanup., Verify that calling ctx.abort() removes worktree cleanly., Verify test run when no automated tests exist in repo. (+14 more)

### Community 9 - "devDependencies"
Cohesion: 0.06
Nodes (32): autoprefixer, lucide-react, postcss, react, react-dom, tailwindcss, @types/react, @types/react-dom (+24 more)

### Community 10 - "find_suggestions"
Cohesion: 0.10
Nodes (31): Collection, fetch_ci_failure_log(), find_suggestions(), get_failing_pr(), Any, CompletedProcess, Path, Run a subprocess command safely without shell redirection. Enforces typed… (+23 more)

### Community 11 - "CDPResponse"
Cohesion: 0.22
Nodes (10): BaseCDPResponse, CDPResponse, Antigravity Chrome DevTools Protocol (CDP) Escalation Bridge. Connects to…, CDP response with explicit error field support., CDPResponse, EscalateRequest, Response from Antigravity Chrome DevTools Protocol bridge., Request payload to escalate a worktree to Antigravity Senior Review via CDP. (+2 more)

### Community 12 - "Workspace Agent Router — Jules Curator Hub"
Cohesion: 0.40
Nodes (4): 📖 [ALL AGENTS] Repository Documentation Index, 🛡️ [ALL AGENTS] Worktree Isolation & Safety Directives, 🛠️ [MASTER AGENT ONLY] Curator CLI Reference, Workspace Agent Router — Jules Curator Hub

### Community 13 - "create_app"
Cohesion: 0.13
Nodes (19): FastAPI, create_app(), Path, Create and configure the Jules Hub FastAPI application., Verify GET / returns JSON status when UI is not built., Verify GET / serves index.html and SPA fallback when ui/dist exists., test_conditional_ui_mount_built(), test_conditional_ui_mount_not_built() (+11 more)

### Community 14 - "models.py"
Cohesion: 0.13
Nodes (26): Enum, Jules Hub FastAPI Server. Provides REST and SSE endpoints for worktree…, Atomic JSON store for Jules Hub configuration and runtime state. Persists…, Jules Hub Multi-Engine Router: Flash, Local Ollama, and Hybrid execution.…, EngineMode, HubConfig, OllamaInstance, Pydantic v2 Data Models for Jules Hub. Defines schemas for engine… (+18 more)

### Community 15 - "compilerOptions"
Cohesion: 0.09
Nodes (22): DOM, DOM.Iterable, ES2020, src, compilerOptions, allowImportingTsExtensions, isolatedModules, jsx (+14 more)

### Community 16 - "Contributing to Jules MCP Server"
Cohesion: 0.50
Nodes (3): Contributing to Jules MCP Server, Development Setup, Pull Request Guidelines

### Community 17 - "execute_run_task"
Cohesion: 0.22
Nodes (6): execute_run_task(), Any, Executes patch generation and test validation inside an isolated worktree., RunRequest, RunResponse, TaskStatus

### Community 18 - "Tasks"
Cohesion: 0.18
Nodes (10): Automatic Multi-Domain Audit Matrix (Stage 1 & Stage 2), Domain Skills & Sub-Agent Roster (N-Domain Mapping), Global Constraints, Jules Hub Implementation Plan (Junior/Senior Coder Pipeline), Task 1: Backend Core — Packaging, Data Models, Scanner & WorktreeManager, Task 2: Backend — Multi-Engine Router (Flash, Local Ollama, Hybrid), Task 3: Backend — CDP Escalation Bridge, SSE Streaming & FastAPI Server, Task 4: Frontend — Web Cockpit Dashboard (React + Tailwind Dark UI) (+2 more)

### Community 19 - "Specifica Architetturale: Jules Hub (Autonomous Junior Coder & Antigravity Escalation Pipeline)"
Cohesion: 0.20
Nodes (9): 1. Visione di Prodotto & Modello Organizzativo (Junior/Senior Coder), 2. Modalità di Calcolo & Quota Shield (3 Engine Mode), 3. Architettura Tecnica del Backend (`jules-hub`), 4. Interfaccia Web Dashboard (UI/UX), 5. Strategia di Packaging e Deploy (Dockge & GHCR), 6. Piano di Implementazione & Passi Successivi, Componenti Chiave del Backend:, Il Pattern Organizzativo "Junior / Senior Developer" (+1 more)

### Community 20 - "Specifiche Tecniche di Jules Hub v2 - Autonomia del Cockpit"
Cohesion: 0.10
Nodes (19): a) Modalità In-Cockpit Senior Review (Ollama Senior o Antigravity CLI), AI Deep Scanner & Storico Proposte (hub/scanner.py), Architettura File, Persistenza JSON & Contratti API REST, b) Modalità Antigravity IDE Handoff via CDP (:9000), Background Scheduler per Repository (hub/scheduler.py), Componenti React UI, Endpoints, Funzionalità (+11 more)

### Community 21 - "compilerOptions"
Cohesion: 0.22
Nodes (8): vite.config.ts, compilerOptions, allowSyntheticDefaultImports, composite, module, moduleResolution, skipLibCheck, include

### Community 25 - "worktree_manager.py"
Cohesion: 0.29
Nodes (7): cleanup_all(), detect_test_command(), Jules Hub Worktree Manager: Isolated git worktree lifecycle and test execution.…, Execute tests asynchronously inside a worktree with a process group kill…, Module-level cleanup helper., Autodetect the fastest local test command for the repository. 1. Custom repo…, run_tests_async()

### Community 26 - ".get"
Cohesion: 0.40
Nodes (3): Any, Allow dict-like get access for backward compatibility., Allow dict-like subscription access.

### Community 31 - "WorktreeManager"
Cohesion: 0.19
Nodes (9): Any, Path, Manages isolated git worktrees across registered repositories. Supports…, Resolve project name or path against projects_registry.json or direct path., Return all valid git repositories registered in projects_registry.json., Create a new isolated git worktree context with naming:…, Prune and remove a specific worktree by path., Remove and prune all worktrees in worktrees_dir across all registered repos. (+1 more)

### Community 32 - "Jules Hub v2 — Autonomous Cockpit Implementation Plan"
Cohesion: 0.13
Nodes (14): Architecture, CodeGraph Evidence, Detailed Tasks with Exact TDD Steps, Domain 1 (Backend Python & FastAPI Core), Domain 2 (Frontend React + Tailwind Dark UI), Domain Skills & Sub-Agent Roster (N-Domain Mapping), Goal, Jules Hub v2 — Autonomous Cockpit Implementation Plan (+6 more)

### Community 33 - "BaseModel"
Cohesion: 0.15
Nodes (13): BaseModel, EscalateResponse, OllamaProbeResult, PersonaConfig, ProjectInfo, Response returned after attempting Senior Review escalation., Configuration for a curation persona (Bolt, Palette, Sentinel)., Repository info registered in projects_registry.json. (+5 more)

### Community 34 - "WorktreeContext"
Cohesion: 0.18
Nodes (6): Context manager for an isolated git worktree. Supports both synchronous…, Mark session as aborted and clean up immediately., Mark session as successfully completed., Forcefully remove worktree and prune dangling locks., Allow tuple unpacking: (worktree_path, branch) = ctx., WorktreeContext

### Community 35 - "probe_ollama_instance"
Cohesion: 0.18
Nodes (12): probe_ollama_instance(), Any, Probe an Ollama instance endpoint (/api/tags) asynchronously via httpx. Returns…, asyncio, EngineRouter senior review gate enforces scope ceiling, safety, and test checks., Unreachable Ollama endpoint returns structured offline result without raising., Successful Ollama /api/tags response returns model list and online_status=True., CDPBridge returns fallback models and graceful failure when CDP port is closed. (+4 more)

### Community 36 - "BackgroundScheduler"
Cohesion: 0.24
Nodes (9): Periodic curation schedule configuration for a repository., RepoScheduleConfig, BackgroundScheduler, Background asyncio daemon checking repository schedules periodically. Enforces…, Stop background scheduling loop., BackgroundScheduler triggers repo schedule, updates timestamps, and respects…, BackgroundScheduler halts additional worktree spawning when…, test_scheduler_trigger_repo() (+1 more)

### Community 37 - "._loop"
Cohesion: 0.20
Nodes (5): Any, Evaluate due repository schedules and trigger curation., Continuous scheduler evaluation loop running every 60 seconds., Start background scheduling loop., Trigger curation cycle for a repository. Updates schedule timestamps and…

### Community 38 - "run_cmd"
Cohesion: 0.22
Nodes (7): CompletedProcess, Execute subprocess command safely with typed list[str] arguments and…, List active worktrees currently in worktrees_dir., run_cmd(), Verify session creation, tuple unpacking, and worktree verification., test_worktree_session_lifecycle_and_unpacking(), WorktreeSessionInfo

### Community 39 - "TaskLogManager"
Cohesion: 0.29
Nodes (3): In-memory event hub for task log streaming via SSE., TaskLogManager, Queue

### Community 40 - "test_env_vars_override"
Cohesion: 0.67
Nodes (3): MonkeyPatch, Verify environment variable overrides for worktrees dir and registry path., test_env_vars_override()

## Knowledge Gaps
- **107 isolated node(s):** `jules-hub`, `name`, `private`, `version`, `type` (+102 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `EngineRouter` connect `EngineRouter` to `probe_ollama_instance`, `test_api.py`, `TaskLogManager`, `create_app`, `models.py`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Why does `WorktreeManager` connect `WorktreeManager` to `test_api.py`, `run_cmd`, `TaskLogManager`, `test_worktree_manager.py`, `test_env_vars_override`, `create_app`, `models.py`, `worktree_manager.py`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `CDPBridge` connect `CDPBridge` to `probe_ollama_instance`, `test_api.py`, `TaskLogManager`, `CDPResponse`, `create_app`, `models.py`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `EngineRouter` (e.g. with `TaskLogManager` and `EngineMode`) actually correct?**
  _`EngineRouter` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `ConfigStore` (e.g. with `TaskLogManager` and `HubConfig`) actually correct?**
  _`ConfigStore` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `CDPBridge` (e.g. with `TaskLogManager` and `CDPResponse`) actually correct?**
  _`CDPBridge` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 19 inferred relationships involving `TaskLogManager` (e.g. with `CDPBridge` and `CDPResponse`) actually correct?**
  _`TaskLogManager` has 19 INFERRED edges - model-reasoned connections that need verification._