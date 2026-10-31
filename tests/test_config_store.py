"""
Unit tests for hub/config_store.py.
Verifies HubConfig and HubState default initialization, atomic writes,
JSON roundtrips, suggestion filtering state, and Senior Review persistence.
"""

import json
from pathlib import Path
from unittest.mock import patch
import pytest

from hub.config_store import ConfigStore
from hub.models import HubConfig, HubState, OllamaInstance, RoleModelConfig, SeniorReviewResult


def test_config_store_load_save_defaults(tmp_path: Path):
    config_file = tmp_path / "hub_config.json"
    state_file = tmp_path / "hub_state.json"
    store = ConfigStore(config_path=config_file, state_path=state_file)

    # Loading nonexistent files should return default models and create the files
    cfg = store.load_config()
    assert isinstance(cfg, HubConfig)
    assert len(cfg.ollama_instances) >= 2
    assert cfg.ollama_instances[0].name == "GPU Server 24/7"
    assert "192.168.88.117" in cfg.ollama_instances[0].url
    assert cfg.ollama_instances[1].name == "Workstation RTX 5070 Ti"
    assert "100.102.204.70" in cfg.ollama_instances[1].url
    assert cfg.cdp_port == 9000
    assert cfg.senior_config.provider == "cdp"
    assert cfg.senior_config.model_name == "Gemini 4 Argon (Low)"

    # Saving and reloading config
    cfg.max_diff_lines = 40
    store.save_config(cfg)
    reloaded = store.load_config()
    assert reloaded.max_diff_lines == 40

    # State operations
    state = store.load_state()
    assert isinstance(state, HubState)
    assert state.ignored_suggestions == []
    store.add_ignored_suggestion("sig_test_123")
    store.add_ignored_suggestion("sig_test_123")  # Duplicate should not be added twice
    updated_state = store.load_state()
    assert updated_state.ignored_suggestions == ["sig_test_123"]

    # Senior review persistence
    review = SeniorReviewResult(
        verdict="APPROVED",
        simple_explanation="Looks great, atomic diff.",
        security_notes="No security risks found.",
        reviewer_model="Gemini 4 Argon (Low)",
        reviewed_at="2026-10-31T18:00:00Z",
    )
    store.set_task_review("task_999", review)
    fetched_review = store.get_task_review("task_999")
    assert fetched_review is not None
    assert fetched_review.verdict == "APPROVED"
    assert fetched_review.reviewer_model == "Gemini 4 Argon (Low)"
    assert fetched_review.simple_explanation == "Looks great, atomic diff."

    # Non-existent task review
    assert store.get_task_review("non_existent_task") is None


def test_config_store_corrupted_file_handling(tmp_path: Path):
    config_file = tmp_path / "hub_config.json"
    state_file = tmp_path / "hub_state.json"
    config_file.write_text("{invalid json", encoding="utf-8")
    state_file.write_text("invalid json state", encoding="utf-8")

    store = ConfigStore(config_path=config_file, state_path=state_file)
    cfg = store.load_config()
    assert isinstance(cfg, HubConfig)
    assert cfg.cdp_port == 9000

    state = store.load_state()
    assert isinstance(state, HubState)
    assert state.ignored_suggestions == []


def test_config_store_atomic_write_cleanup_on_failure(tmp_path: Path):
    config_file = tmp_path / "hub_config.json"
    store = ConfigStore(config_path=config_file)

    with patch.object(Path, "replace", side_effect=OSError("Disk full")):
        with pytest.raises(OSError):
            store.save_config(HubConfig())

    tmp_files = list(tmp_path.glob("*.tmp"))
    assert len(tmp_files) == 0
