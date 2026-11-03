# Julius Hub (`julius-hub`) Rebranding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

### Dual-Gate Plan Audit Matrix

| Gate | Ruolo / Dominio | Conversation ID | Modello | Esito |
| :--- | :--- | :--- | :--- | :--- |
| **Stage 1** | Backend FastAPI & DevOps Plan Auditor | [`eb6e242b-ed6f-45f5-9c0f-0b598a9f00fc`](conversation://eb6e242b-ed6f-45f5-9c0f-0b598a9f00fc) | `flash` | ✅ Integrato (`CommunitySettings.git_commit_authoring`, fallback annidato in `compose.yaml`) |
| **Stage 1** | Frontend React/TS Plan Auditor | [`c25704b7-d195-4ab4-aebb-23238f998508`](conversation://c25704b7-d195-4ab4-aebb-23238f998508) | `flash` | ✅ Integrato (call site `onRunInJulius`, normalizer select, fallback repo `julius-hub` -> `jules`) |
| **Stage 2** | Sentinel Security & Safety Auditor | [`843aa6dd-5f2f-496f-b863-bfd794bdd979`](conversation://843aa6dd-5f2f-496f-b863-bfd794bdd979) | `inherit` | ✅ **APPROVED** (Zero segreti, container non-root `1000:1000`, grounding e migrazione safe) |

**Goal:** Rimuovere ogni riferimento al marchio registrato "Jules" rinominando il prodotto, l'interfaccia utente, il backend FastAPI, l'infrastruttura container/packaging e il repository GitHub in **Julius Hub (`julius-hub`)**, preservando la directory locale `/home/federico/jules` e la retrocompatibilità con configurazioni/variabili d'ambiente esistenti.

**Architecture:** Intervento coordinato su 3 domini isolati: (1) Backend FastAPI & Pydantic Models ([hub/](file:///home/federico/jules/hub), [tests/](file:///home/federico/jules/tests)) con migrazione trasparente di `GitAuthoringMode` (`jules_only` -> `julius_only`) su `CommunitySettings.git_commit_authoring` e fallback delle variabili d'ambiente `JULIUS_*` -> `JULES_*`; (2) Frontend React/TypeScript ([ui/](file:///home/federico/jules/ui)) con aggiornamento di loghi, titoli, handler e impostazioni; (3) Packaging, Docker, Documentazione e Repository GitHub ([pyproject.toml](file:///home/federico/jules/pyproject.toml), [Dockerfile](file:///home/federico/jules/Dockerfile), [compose.yaml](file:///home/federico/jules/compose.yaml), [.env.example](file:///home/federico/jules/.env.example), [README.md](file:///home/federico/jules/README.md), [CONTRIBUTING.md](file:///home/federico/jules/CONTRIBUTING.md), [.agents/AGENTS.md](file:///home/federico/jules/.agents/AGENTS.md) e rename remoto `cavuminfundo/julius-hub`).

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, React 18, TypeScript, Vite, Docker Compose, GitHub CLI (`gh`).

**Spec:** [2026-11-03-julius-hub-rebranding-design.md](file:///home/federico/jules/docs/superpowers/specs/2026-11-03-julius-hub-rebranding-design.md)

## Global Constraints

- **Local Workspace Directory Invariant**: La cartella locale `/home/federico/jules` NON deve essere spostata o rinominata per non interrompere Syncthing e il workspace IDE attivo.
- **Backward Compatibility**: `CommunitySettings` deve accettare e migrare in automatico il valore legacy `"jules_only"` in `"julius_only"`. Le variabili d'ambiente `JULIUS_DATA_DIR`, `JULIUS_WORKTREES_DIR`, `JULIUS_WORKSPACES_ROOT`, `JULIUS_PORT` devono avere fallback trasparente alle rispettive `JULES_*`.
- **Zero Google/Jules Branding in Git Trailers**: I commit e le PR generate devono usare `Julius <julius@julius-hub.local>` invece di `Jules <jules@google.com>`.

### Domain Skills & Sub-Agent Roster (N-Domain Mapping)

| Dominio | Sub-Agente Dedicato (1:1) | Skill Primaria | Transversal Companions (`lookup.py`) | File Esclusivi Assegnati (File Fencing) |
| :--- | :--- | :--- | :--- | :--- |
| **1. Backend FastAPI & Models** | `backend_fastapi_worker` (`Model: 'flash'`) | `python-fastapi-development` (`/home/federico/skills_library/python-fastapi-development/SKILL.md`) | `ponytail`, `antislop-code` | `hub/__init__.py`, `hub/app.py`, `hub/models.py`, `hub/config_store.py`, `hub/worktree_manager.py`, `hub/engine_router.py`, `hub/scanner.py`, `tests/test_api.py`, `tests/test_config_store.py`, `tests/test_engine_router.py`, `tests/test_scanner.py`, `tests/test_worktree_manager.py` |
| **2. Frontend React/TS UI** | `frontend_react_worker` (`Model: 'flash'`) | `react-nextjs-development` (`/home/federico/skills_library/react-nextjs-development/SKILL.md`) | `antislop-ui`, `ponytail` | `ui/index.html`, `ui/package.json`, `ui/package-lock.json`, `ui/src/types.ts`, `ui/src/api.ts`, `ui/src/App.tsx`, `ui/src/components/Sidebar.tsx`, `ui/src/components/SuggestionCard.tsx`, `ui/src/components/SettingsView.tsx` |
| **3. Container, Packaging & Docs** | `devops_docker_worker` (`Model: 'flash'`) | `docker-expert` (`/home/federico/skills_library/docker-expert/SKILL.md`) | `antislop-code`, `ponytail` | `pyproject.toml`, `compose.yaml`, `Dockerfile`, `.env.example`, `README.md`, `CONTRIBUTING.md`, `.agents/AGENTS.md` |

---

### Task 1: Backend FastAPI, Models & Env Fallback (`backend_fastapi_worker`)

**Files:**
- Modify: [hub/__init__.py](file:///home/federico/jules/hub/__init__.py)
- Modify: [hub/models.py](file:///home/federico/jules/hub/models.py)
- Modify: [hub/config_store.py](file:///home/federico/jules/hub/config_store.py)
- Modify: [hub/worktree_manager.py](file:///home/federico/jules/hub/worktree_manager.py)
- Modify: [hub/app.py](file:///home/federico/jules/hub/app.py)
- Modify: [hub/engine_router.py](file:///home/federico/jules/hub/engine_router.py)
- Modify: [hub/scanner.py](file:///home/federico/jules/hub/scanner.py)
- Test: [tests/test_api.py](file:///home/federico/jules/tests/test_api.py), [tests/test_config_store.py](file:///home/federico/jules/tests/test_config_store.py), [tests/test_engine_router.py](file:///home/federico/jules/tests/test_engine_router.py), [tests/test_scanner.py](file:///home/federico/jules/tests/test_scanner.py), [tests/test_worktree_manager.py](file:///home/federico/jules/tests/test_worktree_manager.py)

**Interfaces:**
- Consumes: Existing `HubConfig`, `CommunitySettings`, `GitAuthoringMode` in [hub/models.py](file:///home/federico/jules/hub/models.py).
- Produces: `GitAuthoringMode.JULIUS_ONLY = "julius_only"` (retaining `JULES_ONLY = "jules_only"` alias and `@field_validator("git_commit_authoring", mode="before")` on `CommunitySettings` converting `"jules_only"` / `GitAuthoringMode.JULES_ONLY` -> `GitAuthoringMode.JULIUS_ONLY`), `"service": "julius-hub"` in `/api/health` and root fallback, `JULIUS_*` env vars with `JULES_*` fallback.

- [ ] **Step 1: Write failing tests in `tests/test_api.py` and `tests/test_config_store.py`**
  Update [tests/test_api.py](file:///home/federico/jules/tests/test_api.py) assertions for `"service": "julius-hub"` and add a test in [tests/test_config_store.py](file:///home/federico/jules/tests/test_config_store.py) verifying `CommunitySettings(git_commit_authoring="jules_only")` and `HubConfig(settings={"git_commit_authoring": "jules_only"})` normalize to `GitAuthoringMode.JULIUS_ONLY` (`"julius_only"`), plus `JULIUS_DATA_DIR` priority over `JULES_DATA_DIR`.

- [ ] **Step 2: Update `hub/models.py`, `hub/config_store.py`, `hub/worktree_manager.py`, `hub/app.py`, and docstrings**
  - In [hub/models.py](file:///home/federico/jules/hub/models.py): define `JULIUS_ONLY = "julius_only"` in `GitAuthoringMode` (retaining `JULES_ONLY = "jules_only"` alias for backward compatibility) and add `@field_validator("git_commit_authoring", mode="before")` on `CommunitySettings` to map `"jules_only"` / `GitAuthoringMode.JULES_ONLY` to `GitAuthoringMode.JULIUS_ONLY`.
  - In [hub/config_store.py](file:///home/federico/jules/hub/config_store.py): `os.getenv("JULIUS_DATA_DIR") or os.getenv("JULES_DATA_DIR")`.
  - In [hub/worktree_manager.py](file:///home/federico/jules/hub/worktree_manager.py): apply `os.getenv("JULIUS_WORKTREES_DIR") or os.getenv("JULES_WORKTREES_DIR")` to both `DEFAULT_WORKTREES_DIR` (line 25) and `WorktreeManager.__init__` (line 300), and `os.getenv("JULIUS_WORKSPACES_ROOT") or os.getenv("JULES_WORKSPACES_ROOT")` (line 331).
  - In [hub/app.py](file:///home/federico/jules/hub/app.py): `title="Julius Hub"`, `"service": "julius-hub"`, check `authoring in (GitAuthoringMode.JULIUS_ONLY, GitAuthoringMode.JULES_ONLY)`, git trailer `Julius <julius@julius-hub.local>`, commit/PR titles with `Julius`.

---

### Task 2: Frontend React/TS UI Rebranding (`frontend_react_worker`)

**Files:**
- Modify: [ui/index.html](file:///home/federico/jules/ui/index.html)
- Modify: [ui/package.json](file:///home/federico/jules/ui/package.json)
- Modify: [ui/package-lock.json](file:///home/federico/jules/ui/package-lock.json)
- Modify: [ui/src/types.ts](file:///home/federico/jules/ui/src/types.ts)
- Modify: [ui/src/api.ts](file:///home/federico/jules/ui/src/api.ts)
- Modify: [ui/src/components/Sidebar.tsx](file:///home/federico/jules/ui/src/components/Sidebar.tsx)
- Modify: [ui/src/components/SuggestionCard.tsx](file:///home/federico/jules/ui/src/components/SuggestionCard.tsx)
- Modify: [ui/src/components/SettingsView.tsx](file:///home/federico/jules/ui/src/components/SettingsView.tsx)
- Modify: [ui/src/App.tsx](file:///home/federico/jules/ui/src/App.tsx)

**Interfaces:**
- Consumes: `/api/config` (`GitAuthoringMode = 'co_authored' | 'julius_only' | 'user_only'`).
- Produces: Rebranded UI components, `onRunInJulius` prop in `SuggestionCard`, `handleRunInJulius` in `App.tsx`, updated `<title>Julius Hub</title>`.

- [ ] **Step 1: Update types, package metadata, and HTML title**
  - [ui/index.html](file:///home/federico/jules/ui/index.html): `<title>Julius Hub</title>`
  - [ui/package.json](file:///home/federico/jules/ui/package.json) & [ui/package-lock.json](file:///home/federico/jules/ui/package-lock.json): `"name": "julius-hub-ui"`
  - [ui/src/types.ts](file:///home/federico/jules/ui/src/types.ts): `export type GitAuthoringMode = 'co_authored' | 'julius_only' | 'user_only';`
  - [ui/src/api.ts](file:///home/federico/jules/ui/src/api.ts): update docstring to `Julius Hub API Client`.

- [ ] **Step 2: Update React components (`Sidebar.tsx`, `SuggestionCard.tsx`, `SettingsView.tsx`, `App.tsx`)**
  - [ui/src/components/Sidebar.tsx](file:///home/federico/jules/ui/src/components/Sidebar.tsx): header brand text `julius`.
  - [ui/src/components/SuggestionCard.tsx](file:///home/federico/jules/ui/src/components/SuggestionCard.tsx): rename `onRunInJules` to `onRunInJulius` in `SuggestionCardProps` and component body; update comment line 20 to `Julius`.
  - [ui/src/components/SettingsView.tsx](file:///home/federico/jules/ui/src/components/SettingsView.tsx):
    - Options: `Co-authored (Julius + User)`, `Julius only` (`value="julius_only"`).
    - Add legacy normalizer on select value: `value={s.git_commit_authoring === ('jules_only' as any) ? 'julius_only' : s.git_commit_authoring}`.
    - Labels: `@julius` PR mention label/description, and `Julius Hub` workspace root description.
  - [ui/src/App.tsx](file:///home/federico/jules/ui/src/App.tsx):
    - Header brand text `julius`.
    - Rename `handleRunInJules` to `handleRunInJulius` and update JSX call site line 660: `onRunInJulius={handleRunInJulius}`.
    - Repository fallback logic in `fetchInitialData`:
      `const preferred = p.value.find((pr) => pr.name === 'julius-hub') ?? p.value.find((pr) => pr.name === 'jules') ?? p.value[0]; if (preferred) setSelectedRepo(preferred.name);`
    - In `handleEscalate`: `const repoName = selectedRepo || 'jules';`

---

### Task 3: Docker, Packaging, Docs & GitHub Repo Rename (`devops_docker_worker` + Master Git/GitHub)

**Files:**
- Modify: [pyproject.toml](file:///home/federico/jules/pyproject.toml)
- Modify: [compose.yaml](file:///home/federico/jules/compose.yaml)
- Modify: [Dockerfile](file:///home/federico/jules/Dockerfile)
- Modify: [.env.example](file:///home/federico/jules/.env.example)
- Modify: [README.md](file:///home/federico/jules/README.md)
- Modify: [CONTRIBUTING.md](file:///home/federico/jules/CONTRIBUTING.md)
- Modify: [.agents/AGENTS.md](file:///home/federico/jules/.agents/AGENTS.md)

**Interfaces:**
- Consumes: Updated env var names `JULIUS_*` and package name `julius-hub`.
- Produces: Updated container/package definitions, documentation, and renamed GitHub repository `cavuminfundo/julius-hub`.

- [ ] **Step 1: Update `pyproject.toml`, `compose.yaml`, `Dockerfile`, `.env.example`**
  - [pyproject.toml](file:///home/federico/jules/pyproject.toml): `name = "julius-hub"`
  - [compose.yaml](file:///home/federico/jules/compose.yaml): service `julius-hub`, `image: ghcr.io/cavuminfundo/julius-hub:latest`, `container_name: julius-hub`, and nested env var fallback:
    `JULIUS_WORKSPACES_ROOT=${JULIUS_WORKSPACES_ROOT:-${JULES_WORKSPACES_ROOT:-/workspaces}}` and volume mount `${JULIUS_WORKSPACES_ROOT:-${JULES_WORKSPACES_ROOT:-/workspaces}}:${JULIUS_WORKSPACES_ROOT:-${JULES_WORKSPACES_ROOT:-/workspaces}}:rw`.
  - [Dockerfile](file:///home/federico/jules/Dockerfile): non-root user `julius` (UID 1000, GID 1000) and `/home/julius/.local/bin`.
  - [.env.example](file:///home/federico/jules/.env.example): `JULIUS_PORT=4100`, `JULIUS_DATA_DIR=./data`, `JULIUS_WORKTREES_DIR=./worktrees`, `JULIUS_WORKSPACES_ROOT=/workspaces`.

- [ ] **Step 2: Update `README.md`, `CONTRIBUTING.md`, `.agents/AGENTS.md`**
  Replace product branding `Jules Hub` / `Jules Curator Hub` with `Julius Hub` / `Julius Curator Hub`, removing references to Google Jules trademark while keeping local filesystem path `/home/federico/jules` accurate where referenced.

- [ ] **Step 3: Rename GitHub repository & update git remote (Master Agent)**
  Execute `gh repo rename julius-hub --yes` in `/home/federico/jules` and verify `git remote -v` points to `git@github.com:cavuminfundo/julius-hub.git`.
