# Julius Hub

[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.95.0-blue.svg)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19-blue.svg)](https://reactjs.org/)
[![Tailwind Dark UI](https://img.shields.io/badge/Tailwind-Dark%20UI-blue.svg)](https://tailwindcss.com/)
[![Docker GHCR](https://img.shields.io/badge/Docker-GHCR-blue.svg)](https://github.com/orgs/cavuminfundo/packages)

## Overview

Julius Hub is an autonomous Junior AI Coder Runner and Tech Lead Cockpit designed to streamline the development process. It follows the Junior/Senior Coder pattern, where Junior personas (Bolt, Palette, Sentinel) execute isolated worktree tasks under 50 lines of code. The Senior Tech Lead supervises, reviews diffs, approves/discards changes, or escalates to the Antigravity IDE via the Chrome DevTools Protocol (CDP) Bridge on port 9000.

## Architecture and Core Components

### Hub Components

- **hub/scanner.py**: Discovers registered repositories.
- **hub/worktree_manager.py**: Manages zero-dirty git worktrees in `/home/federico/jules/worktrees/<repo>-<mode>`.
- **hub/engine_router.py**: Routes tasks to different engines:
  - **Flash**: Cloud Gemini Flash.
  - **Local**: Local Ollama RTX 5070 Ti (`http://localhost:11434`).
  - **Hybrid**: Local pre-screening + Cloud execution with fallback.
- **hub/cdp_bridge.py**: Handles Chrome DevTools Protocol (CDP) bridge for 1-click escalation to Antigravity Senior Coder.
- **hub/app.py**: FastAPI backend on port 4100, serving Server-Sent Events (`/api/events`) for real-time telemetry.

### UI Components

- **ui/**: React + Vite + Tailwind Dark Cockpit served on port 4100.

### CLI Entry Point

- **curator.py**: Provides CLI commands for `run`, `fix-ci`, `knowledge`, `list`, `status`, and `cleanup`.

## Quickstart and Docker Deployment

To deploy Julius Hub using Docker, follow these steps:

1. **Create a `compose.yaml` file**:

    ```yaml
    version: '3.8'

    services:
      julius-hub:
        image: ghcr.io/cavuminfundo/julius-hub:latest
        network_mode: host
        environment:
          - PORT=4100
          - CDP_PORT=9000
          - OLLAMA_HOST=http://localhost:11434
    ```

2. **Run the Docker Compose command**:

    ```bash
    docker-compose up -d
    ```

## Local Development and Testing

For local development and testing, use the following commands:

1. **Sync dependencies**:

    ```bash
    uv sync
    ```

2. **Run tests**:

    ```bash
    uv run pytest tests/ -q
    ```

3. **Start the FastAPI backend**:

    ```bash
    uv run uvicorn hub.app:app --host 0.0.0.0 --port 4100
    ```

## License

Julius Hub is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

---

**Note**: Ensure that all dependencies and configurations are correctly set up before running the application.