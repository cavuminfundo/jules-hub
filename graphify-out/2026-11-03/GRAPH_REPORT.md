# Graph Report - jules  (2026-11-02)

## Corpus Check
- 50 files · ~44,608 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 716 nodes · 1304 edges · 60 communities (37 shown, 23 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 66 edges (avg confidence: 0.61)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4486dbf0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Jules Hub
- ConfigStore
- EngineRouter
- CDPBridge
- test_api.py
- Jules AI Agent - Lessons Learned & Behavioral Memory
- .load_state
- types.ts
- test_worktree_manager.py
- devDependencies
- find_suggestions
- test_api_escalate_port_closed_resilience
- Workspace Agent Router — Jules Curator Hub
- create_app
- models.py
- compilerOptions
- Contributing to Jules MCP Server
- .save_secrets
- Tasks
- Specifica Architetturale: Jules Hub (Autonomous Junior Coder & Antigravity Escalation Pipeline)
- Specifiche Tecniche di Jules Hub v2 - Autonomia del Cockpit
- compilerOptions
- bolt.md
- palette.md
- sentinel.md
- detect_test_command
- Suggestion
- __init__.py
- run_cmd
- Jules Hub v2 — Autonomous Cockpit Implementation Plan
- scanner.py
- WorktreeContext
- test_scheduler_and_senior.py
- 4. Layout dell'UI Officiale di Jules
- BackgroundScheduler
- WorktreeManager
- .escalate_to_antigravity
- Global Constraints
- mock_worktree_manager
- jules-hub
- test_api_projects
- test_api_suggestions_with_filters
- test_api_worktrees_prune_all
- test_api_worktrees_prune_specific
- test_api_run_dry_run
- test_api_run_success_flow
- test_api_run_test_failure_escalation
- test_api_stream_logs
- test_api_stream_not_found
- test_conditional_ui_mount_not_built
- test_conditional_ui_mount_built
- test_cors_middleware
- test_api_sessions_and_tasks
- test_api_settings_secrets_and_config
- test_api_freeform_prompt_run
- test_spa_path_traversal_guard
- test_api_health

## God Nodes (most connected - your core abstractions)
1. `ConfigStore` - 45 edges
2. `EngineRouter` - 37 edges
3. `TaskLogManager` - 34 edges
4. `CDPBridge` - 31 edges
5. `create_app()` - 23 edges
6. `WorktreeManager` - 23 edges
7. `BackgroundScheduler` - 17 edges
8. `find_suggestions()` - 16 edges
9. `compilerOptions` - 16 edges
10. `CDPResponse` - 14 edges

## Surprising Connections (you probably didn't know these)
- `client()` --calls--> `create_app()`  [EXTRACTED]
  tests/test_api.py → hub/app.py
- `test_conditional_ui_mount_built()` --calls--> `create_app()`  [EXTRACTED]
  tests/test_api.py → hub/app.py
- `test_conditional_ui_mount_not_built()` --calls--> `create_app()`  [EXTRACTED]
  tests/test_api.py → hub/app.py
- `test_spa_path_traversal_guard()` --calls--> `create_app()`  [EXTRACTED]
  tests/test_api.py → hub/app.py
- `mock_cdp_bridge()` --calls--> `CDPResponse`  [EXTRACTED]
  tests/test_api.py → hub/cdp_bridge.py

## Import Cycles
- None detected.

## Communities (60 total, 23 thin omitted)

### Community 0 - "Jules Hub"
Cohesion: 0.20
Nodes (9): Architecture and Core Components, CLI Entry Point, Hub Components, Jules Hub, License, Local Development and Testing, Overview, Quickstart and Docker Deployment (+1 more)

### Community 1 - "ConfigStore"
Cohesion: 0.19
Nodes (20): ConfigStore, Atomic JSON store for Jules Hub configuration, runtime state, and secrets.…, Atomic JSON store for HubConfig, HubState, and sensitive secrets., HubConfig, HubState, Global hub configuration persisted to data/hub_config.json., Outcome of Senior Review audit gate., Runtime state persisted to data/hub_state.json. (+12 more)

### Community 2 - "EngineRouter"
Cohesion: 0.05
Nodes (66): EngineMode, apply_hunks_to_content(), count_diff_lines(), EngineRouter, extract_code_from_text(), extract_diff_from_text(), get_git_diff(), Path (+58 more)

### Community 3 - "CDPBridge"
Cohesion: 0.10
Nodes (32): CDPBridge, Bridge to Antigravity Desktop via Chrome DevTools Protocol (CDP). Default…, patch, Verify /api/suggestions returns suggestions list., test_api_suggestions_default(), asyncio, Verify error handling when targets have no webSocketDebuggerUrl., Verify error handling when CDP endpoint returns non-200 status. (+24 more)

### Community 4 - "test_api.py"
Cohesion: 0.25
Nodes (7): Unit tests for Jules Hub FastAPI Server (hub/app.py). Tests REST endpoints…, Verify /api/worktrees returns active worktree sessions., Verify /api/escalate invokes CDPBridge and returns 200., Verify /api/run with background=true schedules background task., test_api_escalate_success(), test_api_run_background(), test_api_worktrees()

### Community 5 - "Jules AI Agent - Lessons Learned & Behavioral Memory"
Cohesion: 0.22
Nodes (8): 1. Jules MCP Native Tool & Single Worker Standard, 2. Infrastruttura Docker Remota & Mappa di Topologia, 3. Gestione Obbligatoria Dual-Phase (Session & PR Management) e Resilienza Errori MCP, 4. Cancellazione Immediata dei Branch Remote & Local dopo il Merge PR, 5. Defensive Timeout and Error Handling in Jules MCP, 6. Mandatory Pre-Compiled Container Images Policy (GHCR), 7. Preference for Stateless HTTP (/rpc) and Stdio Transports Over SSE, Jules AI Agent - Lessons Learned & Behavioral Memory

### Community 6 - ".load_state"
Cohesion: 0.12
Nodes (12): SeniorReviewResult, Load HubState runtime data., Persist HubState atomically., Mark a suggestion as ignored., Save a senior review result., Fetch a stored senior review result., Upsert a session record into HubState., Fetch a session record by task_id. (+4 more)

### Community 7 - "types.ts"
Cohesion: 0.06
Nodes (55): api, ApiError, useTaskLogs(), App(), CardTab, CATEGORY_TABS, MainView, DiffDrawer() (+47 more)

### Community 8 - "test_worktree_manager.py"
Cohesion: 0.14
Nodes (24): Delegate to run_tests_async helper., _init_dummy_git_repo(), asyncio, Path, Unit tests for Jules Hub Worktree Manager (hub/worktree_manager.py). Tests…, Verify session creation, tuple unpacking, and worktree verification., Verify that an exception inside WorktreeContext triggers auto-prune cleanup., Verify that calling ctx.abort() removes worktree cleanly. (+16 more)

### Community 9 - "devDependencies"
Cohesion: 0.06
Nodes (32): autoprefixer, lucide-react, postcss, react, react-dom, tailwindcss, @types/react, @types/react-dom (+24 more)

### Community 10 - "find_suggestions"
Cohesion: 0.14
Nodes (20): Collection, find_suggestions(), Scan repository for concrete micro-improvements across Bolt, Palette, or…, Suggestion, Path, Unit tests for Jules Hub Scanner (hub/scanner.py). Verifies detection of micro-…, Verify Bolt detects performance bottlenecks., Verify mode and category filters correctly partition results. (+12 more)

### Community 12 - "Workspace Agent Router — Jules Curator Hub"
Cohesion: 0.40
Nodes (4): 📖 [ALL AGENTS] Repository Documentation Index, 🛡️ [ALL AGENTS] Worktree Isolation & Safety Directives, 🛠️ [MASTER AGENT ONLY] Curator CLI Reference, Workspace Agent Router — Jules Curator Hub

### Community 13 - "create_app"
Cohesion: 0.16
Nodes (16): create_app(), Path, Create and configure the Jules Hub FastAPI application., Path, Scanner filters out suggestions whose IDs are present in ignored_ids., Test GET and PUT on /api/config., Test /api/ollama/test, /api/ollama/instances/{id}/models, and /api/cdp/models., Test discarding suggestion marks it in state and filters from subsequent scans. (+8 more)

### Community 14 - "models.py"
Cohesion: 0.05
Nodes (56): BaseCDPResponse, BaseModel, Enum, FastAPI, execute_run_task(), Any, Jules Hub FastAPI Server. Provides REST and SSE endpoints for worktree…, In-memory event hub for task log streaming via SSE. (+48 more)

### Community 15 - "compilerOptions"
Cohesion: 0.09
Nodes (22): DOM, DOM.Iterable, ES2020, src, compilerOptions, allowImportingTsExtensions, isolatedModules, jsx (+14 more)

### Community 16 - "Contributing to Jules MCP Server"
Cohesion: 0.50
Nodes (3): Contributing to Jules MCP Server, Development Setup, Pull Request Guidelines

### Community 17 - ".save_secrets"
Cohesion: 0.13
Nodes (12): CommunitySettings, mask_secret(), Path, Atomically persist secrets with 0600 permissions and return updated masked…, Load HubConfig, populating secret presence and masked representations., Enrich CommunitySettings with secrets status without exposing plaintext., Persist HubConfig atomically., Mask a token or API key for safe exposure in read endpoints. (+4 more)

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

### Community 25 - "detect_test_command"
Cohesion: 0.50
Nodes (4): detect_test_command(), Execute tests asynchronously inside a worktree with a process group kill…, Autodetect the fastest local test command for the repository. 1. Custom repo…, run_tests_async()

### Community 26 - "Suggestion"
Cohesion: 0.33
Nodes (5): Any, Allow dict-like subscription access., A single micro-improvement suggestion generated by the scanner., Allow dict-like get access for backward compatibility., Suggestion

### Community 31 - "run_cmd"
Cohesion: 0.19
Nodes (8): Any, CompletedProcess, Path, Return all valid git repositories registered in projects_registry.json or…, Execute subprocess command safely with typed list[str] arguments and…, Prune and remove a specific worktree by path., Remove and prune all worktrees in worktrees_dir across all registered repos., run_cmd()

### Community 32 - "Jules Hub v2 — Autonomous Cockpit Implementation Plan"
Cohesion: 0.13
Nodes (14): Architecture, CodeGraph Evidence, Detailed Tasks with Exact TDD Steps, Domain 1 (Backend Python & FastAPI Core), Domain 2 (Frontend React + Tailwind Dark UI), Domain Skills & Sub-Agent Roster (N-Domain Mapping), Goal, Jules Hub v2 — Autonomous Cockpit Implementation Plan (+6 more)

### Community 33 - "scanner.py"
Cohesion: 0.25
Nodes (10): fetch_ci_failure_log(), get_failing_pr(), Any, CompletedProcess, Path, Jules Hub Scanner: Repository inspection and issue suggestion engine. Extracts…, Run a subprocess command safely without shell redirection. Enforces typed…, Fetch PR details and checks status using GitHub CLI ('gh'). Uses list[str]… (+2 more)

### Community 34 - "WorktreeContext"
Cohesion: 0.18
Nodes (6): Context manager for an isolated git worktree. Supports both synchronous…, Mark session as aborted and clean up immediately., Mark session as successfully completed., Forcefully remove worktree and prune dangling locks., Allow tuple unpacking: (worktree_path, branch) = ctx., WorktreeContext

### Community 35 - "test_scheduler_and_senior.py"
Cohesion: 0.12
Nodes (22): probe_ollama_instance(), Any, Probe an Ollama instance endpoint (/api/tags) asynchronously via httpx. Returns…, Periodic curation schedule configuration for a repository., RepoScheduleConfig, Background scheduler for autonomous repository curation. Periodically scans…, asyncio, Comprehensive unit tests for: - probe_ollama_instance and CDPBridge (model… (+14 more)

### Community 36 - "4. Layout dell'UI Officiale di Jules"
Cohesion: 0.20
Nodes (9): 1. Rimozione Completa di `curator.py` e Migrazione dei Test CLI, 2. Zero Hardcoding & Impostazioni Comunità, 3 Tabs, 3. Zero Mock Production Backend, 4. Layout dell'UI Officiale di Jules, Centro (Card Minimale), Input Box per Prompt Free-form, Sidebar Sinistra (Collassabile) (+1 more)

### Community 37 - "BackgroundScheduler"
Cohesion: 0.19
Nodes (8): BackgroundScheduler, Any, Evaluate due repository schedules and trigger curation., Continuous scheduler evaluation loop running every 60 seconds., Background asyncio daemon checking repository schedules periodically. Enforces…, Start background scheduling loop., Stop background scheduling loop., Trigger curation cycle for a repository. Scans for real candidates via…

### Community 38 - "WorktreeManager"
Cohesion: 0.15
Nodes (11): cleanup_all(), Manages isolated git worktrees across registered repositories. Supports…, Resolve project name or path against projects_registry.json,…, Create a new isolated git worktree context with naming:…, List active worktrees currently in worktrees_dir., Module-level cleanup helper., WorktreeManager, MonkeyPatch (+3 more)

### Community 39 - ".escalate_to_antigravity"
Cohesion: 0.25
Nodes (5): EscalateRequest, Escalate a worktree review request to Antigravity Desktop via CDP…, Query Antigravity Model Picker via CDP Runtime.evaluate or return default…, Select senior model in Antigravity DOM and trigger Senior Review via CDP…, Query http://{cdp_host}:{cdp_port}/json/list to find the target…

### Community 40 - "Global Constraints"
Cohesion: 0.29
Nodes (6): Domain Skills & Sub-Agent Roster (N-Domain Mapping), Global Constraints, Jules Hub v3 (Zero Mock, Community-Ready & Official Jules UI) Implementation Plan, Task 1: Purge `curator.py`, Remove Hardcoding & Upgrade Community Config Store, Task 2: Zero-Mock Production Backend (Real Diff, Real Senior Review, Real PR, Free-Form Prompts & Categories), Task 3: Official `jules.google.com` Minimalist Frontend & 4-Section Community Settings

### Community 41 - "mock_worktree_manager"
Cohesion: 0.33
Nodes (6): client(), mock_cdp_bridge(), mock_engine_router(), mock_worktree_manager(), fixture, Path

## Knowledge Gaps
- **123 isolated node(s):** `jules-hub`, `name`, `private`, `version`, `type` (+118 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **23 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ConfigStore` connect `ConfigStore` to `test_scheduler_and_senior.py`, `BackgroundScheduler`, `.load_state`, `create_app`, `models.py`, `.save_secrets`?**
  _High betweenness centrality (0.076) - this node is a cross-community bridge._
- **Why does `EngineRouter` connect `EngineRouter` to `ConfigStore`, `test_scheduler_and_senior.py`, `test_api.py`, `create_app`, `models.py`?**
  _High betweenness centrality (0.071) - this node is a cross-community bridge._
- **Why does `WorktreeManager` connect `WorktreeManager` to `test_api.py`, `test_worktree_manager.py`, `create_app`, `models.py`, `run_cmd`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `ConfigStore` (e.g. with `TaskLogManager` and `CommunitySettings`) actually correct?**
  _`ConfigStore` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `EngineRouter` (e.g. with `TaskLogManager` and `EngineMode`) actually correct?**
  _`EngineRouter` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 23 inferred relationships involving `TaskLogManager` (e.g. with `CDPBridge` and `CDPResponse`) actually correct?**
  _`TaskLogManager` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `CDPBridge` (e.g. with `TaskLogManager` and `CDPResponse`) actually correct?**
  _`CDPBridge` has 3 INFERRED edges - model-reasoned connections that need verification._