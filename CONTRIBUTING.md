# Contributing to Julius Hub

Thank you for considering contributing to `julius-hub`! Contributions are welcome from the community.

## Development Setup

1. **Fork and Clone**:
   ```bash
   git clone https://github.com/your-username/julius-hub.git
   cd julius-hub
   ```

2. **Environment & Dependencies**:
   Ensure you have [uv](https://github.com/astral-sh/uv) or Python 3.10+ installed.
   ```bash
   uv sync
   ```

3. **Running the Server Locally**:
   ```bash
   uv run uvicorn hub.app:app --host 0.0.0.0 --port 4100
   ```

## Pull Request Guidelines

- **Branch Naming**: Use descriptive branch names like `feature/add-activity-filter` or `fix/httpx-timeout`.
- **Code Style & Formatting**: Follow PEP8 conventions.
- **Commit Messages**: Follow [Conventional Commits](https://www.conventionalcommits.org/) (e.g. `feat(hub): ...`, `fix(api): ...`, `docs(readme): ...`).
- **PR Description**: Describe the problem solved, changes introduced, and how to test.
