# Jules Hub v3 (Zero Mock, Community-Ready & Official Jules UI) Implementation Plan

| Audit Stage | Role / Domain | Conversation ID | Verdict | Key Rulings Integrated |
|---|---|---|---|---|
| **Stage 1 (Backend & Architecture)** | `backend_plan_auditor` (`python-fastapi-development` + `ponytail` + `antislop-code`) | `conversation://5feea853-7c0a-4b18-a538-4b786f74ef12` | **APPROVED** | Add `prompt: Optional[str] = None` to `RunRequest`; purge `curator.py`; replace all `/home/federico` and LAN IPs with env vars and `localhost:11434`. |
| **Stage 1 (Frontend & UI)** | `frontend_plan_auditor` (`react-nextjs-development` + `antislop-ui` + `antislop-layoutmobile`) | `conversation://960ad4d6-805c-43a3-a173-0c23286fe939` | **APPROVED** | Official `jules.google.com` dark theme (`#141418`, `zinc-400` WCAG AA contrast), zero decorative emojis, 44x44px touch targets, off-canvas mobile sidebar. |
| **Stage 2 (Sentinel Gate)** | `sentinel_auditor` (`security-audit` + `unslop-review`) | `conversation://73591665-5994-4b25-b0fd-122191183d59` | **APPROVED** | `NamedTemporaryFile` + `0600` + `os.replace` for `hub_secrets.json`; pass `GH_TOKEN`/`GITHUB_TOKEN` only via subprocess `env` dict or HTTP header (never CLI args); `.is_relative_to(dist_dir)` path traversal check in SPA fallback. |

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform Jules Hub into a 100% production-ready, zero-mock, community-friendly autonomous coding cockpit featuring the official minimalist `jules.google.com` interface, complete removal of legacy `curator.py`, configurable API/GitHub credentials in Settings, and real PR/session execution.

**Architecture:**
1. **Legacy Purge & Community Config (`hub/models.py`, `hub/config_store.py`, `hub/worktree_manager.py`, `Dockerfile`, `compose.yaml`, `.env.example`):** Delete `curator.py` and `tests/test_curator.py`, remove all hardcoded `/home/federico` and private LAN IP defaults (`192.168.88.117`, `100.102.204.70`), and extend `HubConfig` with community settings (`github_token_configured`, `cloud_api_key_configured`, `git_commit_authoring`, `export_as_pr`, `open_pr_as_draft`, `only_respond_to_mentions`, `auto_find_issues`, `cdp_url`, `workspaces_root`, `session_history`). Secrets are stored masked in API responses and persisted securely in `.env` / `data/hub_secrets.json` (`0600`).
2. **Zero-Mock Production Backend (`hub/engine_router.py`, `hub/scanner.py`, `hub/scheduler.py`, `hub/app.py`):**
   - Replace fake `create-pr` URL (`https://github.com/example/jules/pull/...`) with real `git push -u origin <branch>` + `gh pr create` (or GitHub REST API fallback using configured token) respecting draft and co-authoring settings.
   - Replace fake `+ sample diff` and fake heuristic `run_senior_review` with real worktree `git diff` extraction and real AI Senior Review via Ollama, Cloud API (Gemini/OpenAI-compatible), or CDP Bridge.
   - Support free-form user prompt execution (`POST /api/sessions` / `POST /api/run` with `prompt` without requiring a pre-existing suggestion) and persist recent sessions (`SessionRecord`) in `hub_state.json`.
   - Upgrade `hub/scanner.py` with optional AI-assisted codebase overview & suggestion enrichment alongside fast AST/pattern rules mapped to the 6 official Jules categories (`all`, `cleanup`, `performance`, `security`, `code_health`, `testing`).
   - Make `hub/scheduler.py` execute real background curation runs when triggered.
3. **Official `jules.google.com` Minimalist UI (`ui/src/`):**
   - **Left Collapsible Sidebar (`Sidebar.tsx`):** Search bar (`Search for repo or sessions`), collapsible `Recent sessions` list (showing real executed tasks/prompts and their status), and collapsible `Codebases` list (`owner/repo`).
   - **Minimal Top Header:** Logo (`jules`), Model badge/selector, theme/status indicator, and Settings icon button.
   - **Central Session Container (`App.tsx`):**
     - Repo selector pill (`owner/repo expand_more`) + `Configure repo` button.
     - Free-form Prompt Box (`Help me fix this error ...` with `->` submit button) that launches an isolated worktree session on any prompt.
     - 3 Native Tabs inside the central card:
       1. `Codebase overview`: Toggle `Automatically find issues in your codebase` + `Schedule skill-based agents` pills (`Performance`, `Design`, `Security`).
       2. `Suggested`: Category filter pills (`All`, `Cleanup`, `Performance`, `Security`, `Code Health`, `Testing`) + compact single-line rows (category icon, title, category badge, impact bars, `Start` button, discard `x` button).
       3. `Scheduled`: Scheduled tasks list or empty state (`No scheduled tasks yet — Schedule tasks to run automatically at specific times`) + quick skill agent buttons (`Performance`, `Design`, `Security`).
   - **Official 4-Tab Settings Page (`SettingsView.tsx`):** Left sub-navigation (`General`, `Integrations`, `MCP`, `API Key`) and right form matching `jules.google.com/settings`: Model settings, Export settings (`Export as pull request`), Git commit authoring (`Co-authored (Jules + User)`), Pull Request settings (`Only respond to comments that mention @jules`, `Open pull requests as drafts by default`), Integrations (GitHub Token / `gh` CLI status, Workspaces root), MCP/CDP configuration, and API Keys & Ollama Cluster management.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, httpx, React 19, TypeScript, Tailwind CSS v4, Lucide React, pytest, Vitest/tsc.

**Spec:** `docs/superpowers/specs/2026-11-02-jules-hub-v3-production-ui-design.md`

## Global Constraints
- Zero hardcoded user paths (`/home/federico`) or private LAN IPs in source code, `Dockerfile`, `compose.yaml`, or default configs.
- Zero plaintext secrets returned over `GET /api/config`: API keys and GitHub tokens are write-only in `PUT /api/config` (or `POST /api/settings/secrets`) and exposed only as boolean/masked status (`has_github_token`, `has_cloud_api_key`).
- All subprocess calls MUST use `list[str]` with `shell=False`.
- Legacy `curator.py` and `tests/test_curator.py` MUST be deleted completely.

### Domain Skills & Sub-Agent Roster (N-Domain Mapping)
| Domain | Primary Skill | Transversal Companions | Dedicated Sub-Agent | Exclusive File Scope |
|---|---|---|---|---|
| **Domain 1: Backend Engine, Zero-Mock & Community Config** | `python-fastapi-development` | `ponytail`, `antislop-code` | `backend_v3_worker` (`Model: 'pro'` — High-Density >=3 interdependent files >400L) | `hub/models.py`, `hub/config_store.py`, `hub/worktree_manager.py`, `hub/scanner.py`, `hub/engine_router.py`, `hub/scheduler.py`, `hub/app.py`, `Dockerfile`, `compose.yaml`, `.env.example`, `curator.py` (delete), `tests/test_*.py` |
| **Domain 2: Official Jules Minimalist UI & Settings** | `react-nextjs-development` | `antislop-ui`, `antislop-layoutmobile` | `frontend_v3_worker` (`Model: 'pro'` — High-Density >=3 interdependent UI components) | `ui/src/types.ts`, `ui/src/api.ts`, `ui/src/App.tsx`, `ui/src/components/Sidebar.tsx`, `ui/src/components/SettingsView.tsx`, `ui/src/components/DiffDrawer.tsx`, `ui/src/components/SuggestionCard.tsx`, `ui/src/components/SchedulerPanel.tsx` |

---

### Task 1: Purge `curator.py`, Remove Hardcoding & Upgrade Community Config Store

**Files:**
- Delete: `curator.py`, `tests/test_curator.py`
- Create: `.env.example`
- Modify: `Dockerfile`, `compose.yaml`, `hub/models.py`, `hub/config_store.py`, `hub/worktree_manager.py`
- Test: `tests/test_config_store.py`, `tests/test_worktree_manager.py`

**Interfaces:**
- Produces in `hub/models.py`:
  - `GitAuthoringMode(str, Enum)`: `"co_authored"`, `"jules_only"`, `"user_only"`
  - `CommunitySettings(BaseModel)`: `default_model: str`, `auto_find_issues: bool`, `export_as_pr: bool`, `git_commit_authoring: GitAuthoringMode`, `only_respond_to_mentions: bool`, `open_pr_as_draft: bool`, `cdp_url: str`, `workspaces_root: str`, `github_token_masked: Optional[str]`, `cloud_api_key_masked: Optional[str]`, `has_github_token: bool`, `has_cloud_api_key: bool`
  - `SecretsUpdateRequest(BaseModel)`: `github_token: Optional[str] = None`, `gemini_api_key: Optional[str] = None`, `openai_api_key: Optional[str] = None`
  - `SessionRecord(BaseModel)`: `task_id: str`, `repo: str`, `title: str`, `prompt: Optional[str] = None`, `persona: str`, `status: TaskStatus`, `branch: Optional[str] = None`, `worktree_path: Optional[str] = None`, `diff: Optional[str] = None`, `pr_url: Optional[str] = None`, `created_at: str`
  - Updated `HubConfig`: default `ollama_instances` uses `http://localhost:11434` (no hardcoded LAN IPs), includes `settings: CommunitySettings`.
  - Updated `HubState`: includes `sessions: List[SessionRecord] = Field(default_factory=list)` and `task_diffs: Dict[str, str] = Field(default_factory=dict)`.

- [ ] **Step 1: Delete `curator.py` and `tests/test_curator.py`, update `Dockerfile`, `compose.yaml`, and `.env.example`**
  - Remove `COPY curator.py ./` from `Dockerfile` and replace user `federico` with `jules` (UID 1000).
  - Update `compose.yaml` to use environment variables `${JULES_WORKSPACES_ROOT:-/workspaces}` instead of `/home/federico`.
  - Create `.env.example` documenting `JULES_PORT`, `JULES_DATA_DIR`, `JULES_WORKTREES_DIR`, `JULES_WORKSPACES_ROOT`, `PROJECTS_REGISTRY_PATH`, `OLLAMA_HOST`, `CDP_URL`, `GITHUB_TOKEN`, `GEMINI_API_KEY`.

- [ ] **Step 2: Write failing tests in `tests/test_config_store.py`**
  - Test that default `HubConfig` has no private IPs (`192.168.` or `100.102.`) and includes `CommunitySettings`.
  - Test secret storage (`save_secrets` / `get_secret` / masked representation) with `0600` file permissions and session history persistence (`upsert_session`, `list_sessions`).

- [ ] **Step 3: Implement `CommunitySettings`, `SessionRecord`, and secret management in `hub/models.py`, `hub/config_store.py`, and `hub/worktree_manager.py`**
  - Use dynamic paths (`Path(os.getenv("JULES_DATA_DIR", Path.cwd() / "data"))`, `Path(os.getenv("JULES_WORKTREES_DIR", Path.cwd() / "worktrees"))`, and auto-discover git repos in `JULES_WORKSPACES_ROOT` if `projects_registry.json` is absent).

---

### Task 2: Zero-Mock Production Backend (Real Diff, Real Senior Review, Real PR, Free-Form Prompts & Categories)

**Files:**
- Modify: `hub/scanner.py`, `hub/engine_router.py`, `hub/scheduler.py`, `hub/app.py`
- Test: `tests/test_api.py`, `tests/test_scheduler_and_senior.py`, `tests/test_scanner.py`

**Interfaces:**
- Produces in `hub/scanner.py`:
  - `find_suggestions(repo_path, mode="all", category="all", ignored_ids=None)` supporting official Jules categories: `"all"`, `"cleanup"`, `"performance"`, `"security"`, `"code_health"`, `"testing"` (while maintaining backward compatibility with `"hygiene"` and `"tests"`).
  - Removes hardcoded `/home/federico/skills_library/...` path in `fetch_ci_failure_log` (uses env var `LOCAL_LLM_OFFLOAD_SCRIPT` if set).
- Produces in `hub/engine_router.py`:
  - Free-form prompt patching `run_freeform_prompt(repo_path: Path, prompt: str, mode: EngineMode) -> PatchResult` when `target_file` is omitted.
  - Real `run_senior_review`: when `provider == "cdp"`, invokes `cdp_bridge.escalate_to_antigravity` or falls back to configured Cloud API (`GEMINI_API_KEY`) / active Ollama instance with a real LLM review prompt; never returns fake static approval without evaluating the real diff.
- Produces in `hub/app.py`:
  - Persists `SessionRecord` and real `git diff` from the worktree in `config_store` on every `/api/run` execution.
  - `GET /api/sessions`: returns recent `SessionRecord` list (filtered optionally by `repo`).
  - `GET /api/tasks/{task_id}`: returns full `SessionRecord` including real `diff` and `worktree_path`.
  - `POST /api/tasks/{task_id}/senior-review`: loads the real stored worktree diff for `task_id` if `diff_text` is not passed in body (eliminating `"+ sample diff"`).
  - `POST /api/tasks/{task_id}/create-pr`: after verifying `review.verdict == "APPROVED"`, executes real git commit (with `Co-authored-by:` if `git_commit_authoring == "co_authored"`), `git push -u origin <branch>`, and `gh pr create` (with `--draft` if `open_pr_as_draft` is enabled, using `GITHUB_TOKEN` from `config_store` secrets or env). In test mode or when `dry_run` / mock transport is injected, returns structured result cleanly.
  - `POST /api/settings/secrets`: saves `GITHUB_TOKEN` / `GEMINI_API_KEY` / `OPENAI_API_KEY` into `config_store` (`0600`) and returns updated masked `CommunitySettings`.

- [ ] **Step 1: Write failing tests in `tests/test_scheduler_and_senior.py` and `tests/test_api.py`**
  - Test `GET /api/sessions` and `GET /api/tasks/{task_id}` returning real worktree diff.
  - Test `POST /api/ settings/secrets` masking tokens and never leaking plaintext in `GET /api/config`.
  - Test free-form prompt execution via `POST /api/run` (`prompt="Fix unused import in app.py"`).
  - Test `trigger_repo` in `BackgroundScheduler` actually scanning suggestions and recording last run status.

- [ ] **Step 2: Implement zero-mock logic in `hub/scanner.py`, `hub/engine_router.py`, `hub/scheduler.py`, and `hub/app.py`**

---

### Task 3: Official `jules.google.com` Minimalist Frontend & 4-Section Community Settings

**Files:**
- Create: `ui/src/components/Sidebar.tsx`
- Modify: `ui/src/types.ts`, `ui/src/api.ts`, `ui/src/App.tsx`, `ui/src/components/SettingsView.tsx`, `ui/src/components/SuggestionCard.tsx`, `ui/src/components/SchedulerPanel.tsx`, `ui/src/components/DiffDrawer.tsx`

**Interfaces:**
- `ui/src/components/Sidebar.tsx`:
  - Collapsible left panel (`260px` wide on desktop, drawer on mobile) matching Screenshot 3:
    - Search input: `Search for repo or sessions`
    - Collapsible `Recent sessions` section: lists sessions from `GET /api/sessions` (clicking a session opens `DiffDrawer` with its real diff, logs, and Senior Review / PR actions) or empty state card (`Recent sessions will show up here`).
    - Collapsible `Codebases` section: lists registered repositories with GitHub/folder icon; clicking selects the active codebase.
- `ui/src/App.tsx`:
  - Minimal top header (`48px` height): Left sidebar toggle button + `jules` brand; Right model badge (`Gemini / Local`), Settings gear button (`onClick={() => setView('settings')}`).
  - Main centered container (`max-w-3xl mx-auto px-4 pt-8`):
    - Top bar above card: Repo selector dropdown (`owner/repo expand_more`) on the left, `Configure repo ⚙` link on the right.
    - Central minimalist rounded card (`bg-[#141418] border border-zinc-800/80 rounded-2xl p-4`):
      - Prompt input box (`Help me fix this error ...` / `Write a test that mocks fetch ...`) with right arrow submit button `->` that calls `api.runTask({ repo: selectedRepo, prompt, persona: 'bolt', mode: selectedEngine })`.
      - 3 compact pill tabs below prompt box: `Codebase overview`, `Suggested`, `Scheduled`.
      - **Tab 1 (`Codebase overview`)**: Matches Screenshot 1 — Toggle row `Automatically find issues in your codebase` + bottom bar `Schedule skill-based agents` with `Performance`, `Design`, `Security` quick buttons + active worktrees summary if any exist.
      - **Tab 2 (`Suggested`)**: Matches Screenshot 2 — Category filter pills (`All`, `Cleanup`, `Performance`, `Security`, `Code Health`, `Testing`) + compact single-line rows (`SuggestionRow` inside `SuggestionCard.tsx`) with category icon, title, subtle category badge (`healing`, `speed`, `science`, `security`), green signal bars, `Start` button, and discard icon button. Zero bloated cards!
      - **Tab 3 (`Scheduled`)**: Matches Screenshot 3 & 5 — Compact scheduled list or empty state (`No scheduled tasks yet — Schedule tasks to run automatically at specific times`) + bottom bar `Schedule skill-based agents` (`Performance`, `Design`, `Security`).
- `ui/src/components/SettingsView.tsx`:
  - Matches Screenshot 4 (`jules.google.com/settings`): Left sidebar menu (`General`, `Integrations`, `MCP`, `API Key`) + Right content panel:
    - `General`: Model settings dropdown, Export settings (`Export as pull request` checkbox), Git commit authoring dropdown (`Co-authored (Jules + User)`, `Jules only`, `User only`), Pull Request settings (`Only respond to comments that mention @jules`, `Open pull requests as drafts by default`), and `Salva e chiudi` purple primary button.
    - `Integrations`: Workspaces Root directory & GitHub integration (`gh` CLI / Personal Access Token input masked).
    - `MCP`: Chrome DevTools Protocol (CDP) bridge URL (`http://127.0.0.1:9000`) & Model Picker discovery.
    - `API Key`: Cloud API Key (`GEMINI_API_KEY` / `OPENAI_API_KEY`) masked input + Multi-Instance Ollama Cluster editor (defaulting to `http://localhost:11434`, zero hardcoded private LAN IPs).

- [ ] **Step 1: Update `ui/src/types.ts` and `ui/src/api.ts` with `CommunitySettings`, `SessionRecord`, `getSessions()`, `getTask()`, and `saveSecrets()`**
- [ ] **Step 2: Create `ui/src/components/Sidebar.tsx` and refactor `ui/src/components/SuggestionCard.tsx` to compact `jules.google.com` single-line rows**
- [ ] **Step 3: Refactor `ui/src/components/SettingsView.tsx` to the 4-section official Jules Settings layout and `ui/src/App.tsx` to the centered minimalist Session view**
- [ ] **Step 4: Run `npx tsc --noEmit` and `npm run build` in `ui/` to verify clean compilation and update `ui/dist/`**
