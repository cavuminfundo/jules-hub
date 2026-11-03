"""
Atomic JSON store for Julius Hub configuration, runtime state, and secrets.
Persists HubConfig, HubState, and hub_secrets.json without external database dependencies.
"""

import json
import logging
import os
from pathlib import Path
import tempfile
from typing import Dict, List, Optional, Union

from hub.models import (
    CommunitySettings,
    HubConfig,
    HubState,
    SecretsUpdateRequest,
    SeniorReviewResult,
    SessionRecord,
)

logger = logging.getLogger("hub.config_store")


def mask_secret(secret: Optional[str]) -> Optional[str]:
    """Mask a token or API key for safe exposure in read endpoints."""
    if not secret:
        return None
    s = secret.strip()
    if len(s) >= 8:
        return f"{s[:4]}...{s[-4:]}"
    return "***"


class ConfigStore:
    """Atomic JSON store for HubConfig, HubState, and sensitive secrets."""

    def __init__(
        self,
        config_path: Optional[Union[str, Path]] = None,
        state_path: Optional[Union[str, Path]] = None,
        secrets_path: Optional[Union[str, Path]] = None,
    ):
        base_data_dir = Path(os.getenv("JULIUS_DATA_DIR") or os.getenv("JULES_DATA_DIR") or Path.cwd() / "data").expanduser().resolve()
        self.config_path = Path(config_path).expanduser().resolve() if config_path else base_data_dir / "hub_config.json"
        self.state_path = Path(state_path).expanduser().resolve() if state_path else base_data_dir / "hub_state.json"
        self.secrets_path = Path(secrets_path).expanduser().resolve() if secrets_path else base_data_dir / "hub_secrets.json"

        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.secrets_path.parent.mkdir(parents=True, exist_ok=True)

    def _atomic_write_json(self, target_path: Path, data: dict, mode_0600: bool = False) -> None:
        """Write JSON data atomically using NamedTemporaryFile and os.replace."""
        target_dir = target_path.parent
        target_dir.mkdir(parents=True, exist_ok=True)

        tmp = tempfile.NamedTemporaryFile(
            mode="w",
            dir=target_dir,
            delete=False,
            encoding="utf-8",
            prefix=f".{target_path.name}.",
            suffix=".tmp",
        )
        tmp_name = tmp.name
        try:
            json.dump(data, tmp, indent=2)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp.close()

            if mode_0600:
                os.chmod(tmp_name, 0o600)

            os.replace(tmp_name, target_path)
        except Exception as e:
            if os.path.exists(tmp_name):
                try:
                    os.unlink(tmp_name)
                except OSError:
                    pass
            logger.exception("Failed atomic write to %s: %s", target_path, e)
            raise

    # --- Secrets Management ---

    def get_secrets(self) -> Dict[str, str]:
        """Load persisted secrets merged with active environment variables."""
        secrets: Dict[str, str] = {}
        if self.secrets_path.exists():
            try:
                secrets = json.loads(self.secrets_path.read_text(encoding="utf-8"))
            except Exception as e:
                logger.error("Error reading %s: %s", self.secrets_path, e)

        # Environment variable overrides
        for env_k, sec_k in [
            ("GITHUB_TOKEN", "github_token"),
            ("GH_TOKEN", "github_token"),
            ("GEMINI_API_KEY", "gemini_api_key"),
            ("OPENAI_API_KEY", "openai_api_key"),
        ]:
            val = os.getenv(env_k)
            if val and not secrets.get(sec_k):
                secrets[sec_k] = val

        return secrets

    def save_secrets(self, req: SecretsUpdateRequest) -> CommunitySettings:
        """Atomically persist secrets with 0600 permissions and return updated masked settings."""
        current = self.get_secrets()
        if req.github_token is not None:
            current["github_token"] = req.github_token
        if req.gemini_api_key is not None:
            current["gemini_api_key"] = req.gemini_api_key
        if req.openai_api_key is not None:
            current["openai_api_key"] = req.openai_api_key

        self._atomic_write_json(self.secrets_path, current, mode_0600=True)

        cfg = self.load_config()
        return cfg.settings

    # --- Config Management ---

    def load_config(self) -> HubConfig:
        """Load HubConfig, populating secret presence and masked representations."""
        if not self.config_path.exists():
            cfg = HubConfig()
            self._enrich_settings_with_secrets(cfg)
            self.save_config(cfg)
            return cfg

        try:
            raw = json.loads(self.config_path.read_text(encoding="utf-8"))
            cfg = HubConfig.model_validate(raw)
        except Exception as e:
            logger.error("Error loading config from %s: %s. Returning defaults.", self.config_path, e)
            cfg = HubConfig()

        self._enrich_settings_with_secrets(cfg)
        return cfg

    def _enrich_settings_with_secrets(self, cfg: HubConfig) -> None:
        """Enrich CommunitySettings with secrets status without exposing plaintext."""
        secrets = self.get_secrets()
        gh_tok = secrets.get("github_token") or os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
        cloud_key = (
            secrets.get("gemini_api_key")
            or secrets.get("openai_api_key")
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("OPENAI_API_KEY")
        )

        cfg.settings.has_github_token = bool(gh_tok)
        cfg.settings.github_token_masked = mask_secret(gh_tok)
        cfg.settings.has_cloud_api_key = bool(cloud_key)
        cfg.settings.cloud_api_key_masked = mask_secret(cloud_key)

    def save_config(self, config: HubConfig) -> None:
        """Persist HubConfig atomically."""
        self._atomic_write_json(self.config_path, config.model_dump())

    # --- State & Session Management ---

    def load_state(self) -> HubState:
        """Load HubState runtime data."""
        if not self.state_path.exists():
            default_state = HubState()
            self.save_state(default_state)
            return default_state
        try:
            raw = json.loads(self.state_path.read_text(encoding="utf-8"))
            return HubState.model_validate(raw)
        except Exception as e:
            logger.error("Error loading state from %s: %s. Returning empty state.", self.state_path, e)
            return HubState()

    def save_state(self, state: HubState) -> None:
        """Persist HubState atomically."""
        self._atomic_write_json(self.state_path, state.model_dump())

    def add_ignored_suggestion(self, suggestion_sig: str) -> None:
        """Mark a suggestion as ignored."""
        state = self.load_state()
        if suggestion_sig not in state.ignored_suggestions:
            state.ignored_suggestions.append(suggestion_sig)
            self.save_state(state)

    def set_task_review(self, task_id: str, review: SeniorReviewResult) -> None:
        """Save a senior review result."""
        state = self.load_state()
        state.task_reviews[task_id] = review
        self.save_state(state)

    def get_task_review(self, task_id: str) -> Optional[SeniorReviewResult]:
        """Fetch a stored senior review result."""
        state = self.load_state()
        return state.task_reviews.get(task_id)

    def upsert_session(self, session: SessionRecord) -> None:
        """Upsert a session record into HubState."""
        state = self.load_state()
        existing_idx = next((i for i, s in enumerate(state.sessions) if s.task_id == session.task_id), None)
        if existing_idx is not None:
            state.sessions[existing_idx] = session
        else:
            state.sessions.insert(0, session)

        if session.diff:
            state.task_diffs[session.task_id] = session.diff

        self.save_state(state)

    def get_session(self, task_id: str) -> Optional[SessionRecord]:
        """Fetch a session record by task_id."""
        state = self.load_state()
        return next((s for s in state.sessions if s.task_id == task_id), None)

    def list_sessions(self, repo: Optional[str] = None) -> List[SessionRecord]:
        """List sessions, optionally filtered by repository name."""
        state = self.load_state()
        if not repo:
            return state.sessions
        repo_lower = repo.lower()
        return [s for s in state.sessions if s.repo.lower() == repo_lower or s.repo.lower().endswith(f"/{repo_lower}")]

    def set_task_diff(self, task_id: str, diff_text: str) -> None:
        """Store the diff associated with a task_id."""
        state = self.load_state()
        state.task_diffs[task_id] = diff_text
        for s in state.sessions:
            if s.task_id == task_id:
                s.diff = diff_text
                break
        self.save_state(state)

    def get_task_diff(self, task_id: str) -> Optional[str]:
        """Retrieve stored diff text for a task_id."""
        state = self.load_state()
        return state.task_diffs.get(task_id)
