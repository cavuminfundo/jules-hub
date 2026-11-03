# Graph Report - jules  (2026-11-03)

## Corpus Check
- 52 files · ~46,792 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 758 nodes · 1355 edges · 58 communities (35 shown, 23 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 66 edges (avg confidence: 0.61)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4486dbf0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Julius Hub
- 2. Frontend UI Changes
- EngineRouter
- CDPBridge
- test_api.py
- Jules AI Agent - Lessons Learned & Behavioral Memory
- ConfigStore
- types.ts
- WorktreeManager
- devDependencies
- find_suggestions
- test_api_escalate_port_closed_resilience
- Workspace Agent Router — Julius Curator Hub
- test_scheduler_and_senior.py
- models.py
- compilerOptions
- Contributing to Julius Hub
- app.py
- Tasks
- Specifica Architetturale: Jules Hub (Autonomous Junior Coder & Antigravity Escalation Pipeline)
- Specifiche Tecniche di Jules Hub v2 - Autonomia del Cockpit
- compilerOptions
- bolt.md
- palette.md
- sentinel.md
- TaskLogManager
- .normalize_git_commit_authoring
- __init__.py
- execute_run_task
- Jules Hub v2 — Autonomous Cockpit Implementation Plan
- Global Constraints
- test_api_suggestions_default
- EscalateRequest
- 4. Layout dell'UI Officiale di Jules
- BackgroundScheduler
- worktree_manager.py
- test_api_worktrees
- Global Constraints
- mock_worktree_manager
- test_api_escalate_success
- test_api_projects
- test_api_suggestions_with_filters
- test_api_worktrees_prune_all
- test_api_worktrees_prune_specific
- test_api_run_dry_run
- test_api_run_success_flow
- test_api_run_test_failure_escalation
- test_api_stream_logs
- test_api_run_background
- test_conditional_ui_mount_not_built
- test_conditional_ui_mount_built
- julius-hub
- test_api_freeform_prompt_run
- test_spa_path_traversal_guard
- test_api_health

## God Nodes (most connected - your core abstractions)
1. `ConfigStore` - 46 edges
2. `EngineRouter` - 37 edges
3. `TaskLogManager` - 34 edges
4. `CDPBridge` - 31 edges
5. `WorktreeManager` - 25 edges
6. `create_app()` - 23 edges
7. `BackgroundScheduler` - 17 edges
8. `find_suggestions()` - 16 edges
9. `compilerOptions` - 16 edges
10. `HubConfig` - 15 edges

## Surprising Connections (you probably didn't know these)
- `client()` --calls--> `create_app()`  [EXTRACTED]
  tests/test_api.py → hub/app.py
- `test_conditional_ui_mount_built()` --calls--> `create_app()`  [EXTRACTED]
  tests/test_api.py → hub/app.py
- `test_conditional_ui_mount_not_built()` --calls--> `create_app()`  [EXTRACTED]
  tests/test_api.py → hub/app.py
- `test_spa_path_traversal_guard()` --calls--> `create_app()`  [EXTRACTED]
  tests/test_api.py → hub/app.py
- `test_api_config_routes()` --calls--> `create_app()`  [EXTRACTED]
  tests/test_scheduler_and_senior.py → hub/app.py

## Import Cycles
- None detected.

## Communities (58 total, 23 thin omitted)

### Community 0 - "Julius Hub"
Cohesion: 0.20
Nodes (9): Architecture and Core Components, CLI Entry Point, Hub Components, Julius Hub, License, Local Development and Testing, Overview, Quickstart and Docker Deployment (+1 more)

### Community 1 - "2. Frontend UI Changes"
Cohesion: 0.07
Nodes (27): 1. Goal & Scope, 2. Frontend UI Changes, 3. Backend & Config Compatibility, 4. Docker, Packaging & Docs, 5. GitHub Repository Rename, compose.yaml, Dockerfile, .env.example (+19 more)

### Community 2 - "EngineRouter"
Cohesion: 0.05
Nodes (68): EngineMode, apply_hunks_to_content(), count_diff_lines(), EngineRouter, extract_code_from_text(), extract_diff_from_text(), get_git_diff(), Path (+60 more)

### Community 3 - "CDPBridge"
Cohesion: 0.08
Nodes (38): EscalateRequest, CDPBridge, Escalate a worktree review request to Antigravity Desktop via CDP…, Query Antigravity Model Picker via CDP Runtime.evaluate or return default…, Select senior model in Antigravity DOM and trigger Senior Review via CDP…, Bridge to Antigravity Desktop via Chrome DevTools Protocol (CDP). Default…, Query http://{cdp_host}:{cdp_port}/json/list to find the target…, patch (+30 more)

### Community 4 - "test_api.py"
Cohesion: 0.20
Nodes (9): Unit tests for Julius Hub FastAPI Server (hub/app.py). Tests REST endpoints…, Verify /api/stream/{task_id} returns 404 for unknown task., Verify CORS headers are returned on preflight requests., Verify /api/sessions and /api/tasks/{task_id} endpoints., Verify /api/settings/secrets updates tokens and masks them in /api/config., test_api_sessions_and_tasks(), test_api_settings_secrets_and_config(), test_api_stream_not_found() (+1 more)

### Community 5 - "Jules AI Agent - Lessons Learned & Behavioral Memory"
Cohesion: 0.22
Nodes (8): 1. Jules MCP Native Tool & Single Worker Standard, 2. Infrastruttura Docker Remota & Mappa di Topologia, 3. Gestione Obbligatoria Dual-Phase (Session & PR Management) e Resilienza Errori MCP, 4. Cancellazione Immediata dei Branch Remote & Local dopo il Merge PR, 5. Defensive Timeout and Error Handling in Jules MCP, 6. Mandatory Pre-Compiled Container Images Policy (GHCR), 7. Preference for Stateless HTTP (/rpc) and Stdio Transports Over SSE, Jules AI Agent - Lessons Learned & Behavioral Memory

### Community 6 - "ConfigStore"
Cohesion: 0.06
Nodes (44): CommunitySettings, ConfigStore, mask_secret(), Path, SeniorReviewResult, Atomic JSON store for Julius Hub configuration, runtime state, and secrets.…, Atomically persist secrets with 0600 permissions and return updated masked…, Load HubConfig, populating secret presence and masked representations. (+36 more)

### Community 7 - "types.ts"
Cohesion: 0.06
Nodes (55): api, ApiError, useTaskLogs(), App(), CardTab, CATEGORY_TABS, MainView, DiffDrawer() (+47 more)

### Community 8 - "WorktreeManager"
Cohesion: 0.05
Nodes (51): detect_test_command(), Any, CompletedProcess, Path, Execute tests asynchronously inside a worktree with a process group kill…, Context manager for an isolated git worktree. Supports both synchronous…, Mark session as aborted and clean up immediately., Mark session as successfully completed. (+43 more)

### Community 9 - "devDependencies"
Cohesion: 0.06
Nodes (32): autoprefixer, lucide-react, postcss, react, react-dom, tailwindcss, @types/react, @types/react-dom (+24 more)

### Community 10 - "find_suggestions"
Cohesion: 0.10
Nodes (32): Collection, A single micro-improvement suggestion generated by the scanner., Suggestion, fetch_ci_failure_log(), find_suggestions(), get_failing_pr(), Any, CompletedProcess (+24 more)

### Community 12 - "Workspace Agent Router — Julius Curator Hub"
Cohesion: 0.40
Nodes (4): 📖 [ALL AGENTS] Repository Documentation Index, 🛡️ [ALL AGENTS] Worktree Isolation & Safety Directives, 🛠️ [MASTER AGENT ONLY] Curator CLI Reference, Workspace Agent Router — Julius Curator Hub

### Community 13 - "test_scheduler_and_senior.py"
Cohesion: 0.12
Nodes (23): HubConfig, Periodic curation schedule configuration for a repository., Global hub configuration persisted to data/hub_config.json., RepoScheduleConfig, Background scheduler for autonomous repository curation. Periodically scans…, Path, Comprehensive unit tests for: - probe_ollama_instance and CDPBridge (model…, Scanner filters out suggestions whose IDs are present in ignored_ids. (+15 more)

### Community 14 - "models.py"
Cohesion: 0.11
Nodes (25): BaseModel, Enum, EscalateResponse, GitAuthoringMode, OllamaInstance, OllamaProbeResult, PersonaConfig, ProjectInfo (+17 more)

### Community 15 - "compilerOptions"
Cohesion: 0.09
Nodes (22): DOM, DOM.Iterable, ES2020, src, compilerOptions, allowImportingTsExtensions, isolatedModules, jsx (+14 more)

### Community 16 - "Contributing to Julius Hub"
Cohesion: 0.50
Nodes (3): Contributing to Julius Hub, Development Setup, Pull Request Guidelines

### Community 17 - "app.py"
Cohesion: 0.15
Nodes (16): BaseCDPResponse, FastAPI, create_app(), Path, Julius Hub FastAPI Server. Provides REST and SSE endpoints for worktree…, Create and configure the Julius Hub FastAPI application., CDPResponse, probe_ollama_instance() (+8 more)

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

### Community 25 - "TaskLogManager"
Cohesion: 0.18
Nodes (7): In-memory event hub for task log streaming via SSE., TaskLogManager, Model and provider assignment for Junior or Senior role., RoleModelConfig, Queue, EngineRouter senior review gate enforces scope ceiling, safety, and test checks., test_run_senior_review_gate()

### Community 26 - ".normalize_git_commit_authoring"
Cohesion: 0.29
Nodes (4): field_validator, Any, Allow dict-like get access for backward compatibility., Allow dict-like subscription access.

### Community 31 - "execute_run_task"
Cohesion: 0.22
Nodes (6): execute_run_task(), Any, Executes patch generation and test validation inside an isolated worktree., RunRequest, RunResponse, TaskStatus

### Community 32 - "Jules Hub v2 — Autonomous Cockpit Implementation Plan"
Cohesion: 0.13
Nodes (14): Architecture, CodeGraph Evidence, Detailed Tasks with Exact TDD Steps, Domain 1 (Backend Python & FastAPI Core), Domain 2 (Frontend React + Tailwind Dark UI), Domain Skills & Sub-Agent Roster (N-Domain Mapping), Goal, Jules Hub v2 — Autonomous Cockpit Implementation Plan (+6 more)

### Community 33 - "Global Constraints"
Cohesion: 0.25
Nodes (7): Domain Skills & Sub-Agent Roster (N-Domain Mapping), Dual-Gate Plan Audit Matrix, Global Constraints, Julius Hub (`julius-hub`) Rebranding Implementation Plan, Task 1: Backend FastAPI, Models & Env Fallback (`backend_fastapi_worker`), Task 2: Frontend React/TS UI Rebranding (`frontend_react_worker`), Task 3: Docker, Packaging, Docs & GitHub Repo Rename (`devops_docker_worker` + Master Git/GitHub)

### Community 35 - "EscalateRequest"
Cohesion: 0.20
Nodes (11): EscalateRequest, Request payload to escalate a worktree to Antigravity Senior Review via CDP., asyncio, Unreachable Ollama endpoint returns structured offline result without raising., Successful Ollama /api/tags response returns model list and online_status=True., CDPBridge returns fallback models and graceful failure when CDP port is closed., Mocked CDP WebSocket communication returns success and response_data., test_cdp_model_picker_and_escalate_offline() (+3 more)

### Community 36 - "4. Layout dell'UI Officiale di Jules"
Cohesion: 0.20
Nodes (9): 1. Rimozione Completa di `curator.py` e Migrazione dei Test CLI, 2. Zero Hardcoding & Impostazioni Comunità, 3 Tabs, 3. Zero Mock Production Backend, 4. Layout dell'UI Officiale di Jules, Centro (Card Minimale), Input Box per Prompt Free-form, Sidebar Sinistra (Collassabile) (+1 more)

### Community 37 - "BackgroundScheduler"
Cohesion: 0.19
Nodes (8): BackgroundScheduler, Any, Evaluate due repository schedules and trigger curation., Continuous scheduler evaluation loop running every 60 seconds., Background asyncio daemon checking repository schedules periodically. Enforces…, Start background scheduling loop., Stop background scheduling loop., Trigger curation cycle for a repository. Scans for real candidates via…

### Community 38 - "worktree_manager.py"
Cohesion: 0.33
Nodes (5): Metadata describing an isolated git worktree session., WorktreeSessionInfo, cleanup_all(), Julius Hub Worktree Manager: Isolated git worktree lifecycle and test…, Module-level cleanup helper.

### Community 40 - "Global Constraints"
Cohesion: 0.29
Nodes (6): Domain Skills & Sub-Agent Roster (N-Domain Mapping), Global Constraints, Jules Hub v3 (Zero Mock, Community-Ready & Official Jules UI) Implementation Plan, Task 1: Purge `curator.py`, Remove Hardcoding & Upgrade Community Config Store, Task 2: Zero-Mock Production Backend (Real Diff, Real Senior Review, Real PR, Free-Form Prompts & Categories), Task 3: Official `jules.google.com` Minimalist Frontend & 4-Section Community Settings

### Community 41 - "mock_worktree_manager"
Cohesion: 0.33
Nodes (6): client(), mock_cdp_bridge(), mock_engine_router(), mock_worktree_manager(), fixture, Path

## Knowledge Gaps
- **149 isolated node(s):** `julius-hub`, `name`, `private`, `version`, `type` (+144 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **23 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ConfigStore` connect `ConfigStore` to `BackgroundScheduler`, `test_scheduler_and_senior.py`, `models.py`, `app.py`, `TaskLogManager`?**
  _High betweenness centrality (0.070) - this node is a cross-community bridge._
- **Why does `EngineRouter` connect `EngineRouter` to `test_api.py`, `test_scheduler_and_senior.py`, `models.py`, `app.py`, `TaskLogManager`?**
  _High betweenness centrality (0.065) - this node is a cross-community bridge._
- **Why does `WorktreeManager` connect `WorktreeManager` to `worktree_manager.py`, `app.py`, `test_api.py`, `TaskLogManager`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `ConfigStore` (e.g. with `TaskLogManager` and `CommunitySettings`) actually correct?**
  _`ConfigStore` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `EngineRouter` (e.g. with `TaskLogManager` and `EngineMode`) actually correct?**
  _`EngineRouter` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 23 inferred relationships involving `TaskLogManager` (e.g. with `CDPBridge` and `CDPResponse`) actually correct?**
  _`TaskLogManager` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `CDPBridge` (e.g. with `TaskLogManager` and `CDPResponse`) actually correct?**
  _`CDPBridge` has 3 INFERRED edges - model-reasoned connections that need verification._