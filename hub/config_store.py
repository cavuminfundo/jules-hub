"""
Atomic JSON store for Jules Hub configuration and runtime state.
Persists HubConfig and HubState without database dependencies.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Union

from hub.models import HubConfig, HubState, SeniorReviewResult

logger = logging.getLogger("hub.config_store")


class ConfigStore:
    """
    Atomic JSON store for HubConfig and HubState using pathlib.Path and file rename.
    """

    def __init__(
        self,
        config_path: Optional[Union[str, Path]] = None,
        state_path: Optional[Union[str, Path]] = None,
    ):
        base_data_dir = Path("/home/federico/jules/data")
        self.config_path = Path(config_path) if config_path else base_data_dir / "hub_config.json"
        self.state_path = Path(state_path) if state_path else base_data_dir / "hub_state.json"
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

    def _atomic_write_json(self, target_path: Path, data: dict) -> None:
        tmp_path = target_path.with_name(f"{target_path.name}.tmp")
        try:
            tmp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            tmp_path.replace(target_path)
        except Exception as e:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            logger.exception("Failed atomic write to %s: %s", target_path, e)
            raise

    def load_config(self) -> HubConfig:
        if not self.config_path.exists():
            default_cfg = HubConfig()
            self.save_config(default_cfg)
            return default_cfg
        try:
            raw = json.loads(self.config_path.read_text(encoding="utf-8"))
            return HubConfig.model_validate(raw)
        except Exception as e:
            logger.error("Error loading config from %s: %s. Returning defaults.", self.config_path, e)
            return HubConfig()

    def save_config(self, config: HubConfig) -> None:
        self._atomic_write_json(self.config_path, config.model_dump())

    def load_state(self) -> HubState:
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
        self._atomic_write_json(self.state_path, state.model_dump())

    def add_ignored_suggestion(self, suggestion_sig: str) -> None:
        state = self.load_state()
        if suggestion_sig not in state.ignored_suggestions:
            state.ignored_suggestions.append(suggestion_sig)
            self.save_state(state)

    def set_task_review(self, task_id: str, review: SeniorReviewResult) -> None:
        state = self.load_state()
        state.task_reviews[task_id] = review
        self.save_state(state)

    def get_task_review(self, task_id: str) -> Optional[SeniorReviewResult]:
        state = self.load_state()
        return state.task_reviews.get(task_id)
