# Julius Hub Rebranding Design Specification

## 1. Goal & Scope

### Goal
Rebrand the existing Jules Hub application to Julius Hub (julius-hub) while maintaining the current functionality and user experience.

### Scope
- **Frontend UI**: Update the user interface to reflect the new brand name.
- **Backend**: Ensure compatibility and consistency with the new brand name.
- **Docker/Packaging**: Update Docker configurations and packaging scripts.
- **Documentation**: Revise all documentation to reflect the new brand name.
- **GitHub Repository**: Rename the repository and update remote URLs.

### Exclusions
- Local directory `/home/federico/jules` will remain unchanged.

## 2. Frontend UI Changes

### ui/index.html
- **Title**: Update the title tag to 'Julius Hub'.

### ui/package.json
- **Name**: Change the package name to 'julius-hub-ui'.

### Sidebar.tsx and App.tsx
- **Logo**: Update the logo to 'julius'.

### SuggestionCard.tsx and App.tsx
- **onRunInJulius/handleRunInJulius**: Ensure these methods are updated to reflect the new brand name.

### SettingsView.tsx
- **Authoring Options**: Add new options 'Co-authored (Julius + User)' and 'Julius only' ('julius_only').
- **PR Filter**: Update the PR filter to '@julius'.

### types.ts
- **GitAuthoringMode**: Add a new enum value `GitAuthoringMode.JULIUS_ONLY = 'julius_only'`.

## 3. Backend & Config Compatibility

### hub/app.py
- **Title**: Update the title to 'Julius Hub'.

### Service
- **Name**: Change the service name to 'julius-hub'.

### Git Trailer
- **Trailer**: Update the git trailer to 'Julius <julius@julius-hub.local>'.

### hub/models.py
- **GitAuthoringMode**: Update `GitAuthoringMode.JULIUS_ONLY = 'julius_only'` and add a Pydantic model_validator to migrate legacy 'jules_only' to 'julius_only'.

### hub/config_store.py and hub/worktree_manager.py
- **Environment Variables**: Support `JULIUS_DATA_DIR`, `JULIUS_WORKTREES_DIR`, `JULIUS_WORKSPACES_ROOT` with fallback to `JULES_*`.

## 4. Docker, Packaging & Docs

### pyproject.toml
- **Name**: Change the project name to 'julius-hub'.

### compose.yaml
- **Service Name**: Update the service name to 'julius-hub'.
- **Image**: Change the image to 'ghcr.io/cavuminfundo/julius-hub:latest'.

### Dockerfile
- **User**: Use a non-root user 'julius' with UID 1000.

### .env.example
- **Environment Variables**: Update all environment variables to start with `JULIUS_*`.

### README.md, CONTRIBUTING.md, .agents/AGENTS.md
- **Content**: Update all relevant documentation to reflect the new brand name.

## 5. GitHub Repository Rename

### Repository Name
- **Old Name**: cavuminfundo/jules-hub
- **New Name**: cavuminfundo/julius-hub

### Git Remote Update
- **Command**: `git remote set-url origin https://github.com/cavuminfundo/julius-hub.git`

---

This document outlines the necessary changes to rebrand Jules Hub to Julius Hub while ensuring compatibility and maintaining the current functionality.