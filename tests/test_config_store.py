"""
Unit tests for hub/config_store.py.
Verifies HubConfig and HubState default initialization, atomic writes,
zero private LAN IPs, CommunitySettings, secrets persistence (0600),
and session history management.
"""

import json
import os
from pathlib import Path
import stat
from unittest.mock import patch
import pytest

from hub.config_store import ConfigStore
from hub.models import (
    CommunitySettings,
    GitAuthoringMode,
    HubConfig,
    HubState,
    SecretsUpdateRequest,
    SeniorReviewResult,
    SessionRecord,
    TaskStatus,
)


def test_config_store_load_save_defaults(tmp_path: Path):
    config_file = tmp_path / "hub_config.json"
    state_file = tmp_path / "hub_state.json"
    secrets_file = tmp_path / "hub_secrets.json"
    store = ConfigStore(config_path=config_file, state_path=state_file, secrets_path=secrets_file)

    # Loading nonexistent files should return default models and create the files
    cfg = store.load_config()
    assert isinstance(cfg, HubConfig)
    assert len(cfg.ollama_instances) == 1
    assert cfg.ollama_instances[0].name == "Local Ollama"
    assert cfg.ollama_instances[0].url == "http://localhost:11434"
    # Zero private LAN IPs
    for inst in cfg.ollama_instances:
        assert "192.168." not in inst.url
        assert "100.102." not in inst.url

    # Check CommunitySettings
    assert isinstance(cfg.settings, CommunitySettings)
    assert cfg.settings.default_model == "Gemini 3.1 Pro"
    assert cfg.settings.export_as_pr is True
    assert cfg.settings.git_commit_authoring == GitAuthoringMode.CO_AUTHORED
    assert cfg.settings.has_github_token is False

    # Saving and reloading config
    cfg.max_diff_lines = 40
    store.save_config(cfg)
    reloaded = store.load_config()
    assert reloaded.max_diff_lines == 40


def test_config_store_secrets_persistence_and_masking(tmp_path: Path):
    config_file = tmp_path / "hub_config.json"
    secrets_file = tmp_path / "hub_secrets.json"
    store = ConfigStore(config_path=config_file, secrets_path=secrets_file)

    # Save secrets
    req = SecretsUpdateRequest(
        github_token="ghp_1234567890abcdef",
        gemini_api_key="AIzaSyA_test_key_gemini",
    )
    settings = store.save_secrets(req)
    assert settings.has_github_token is True
    assert settings.github_token_masked == "ghp_...cdef"
    assert settings.has_cloud_api_key is True
    assert "AIza...mini" in settings.cloud_api_key_masked

    # Verify secrets file exists with 0600 permissions
    assert secrets_file.exists()
    mode = stat.S_IMODE(secrets_file.stat().st_mode)
    assert mode == 0o600

    # Ensure get_secrets returns full plaintext internally
    sec = store.get_secrets()
    assert sec["github_token"] == "ghp_1234567890abcdef"
    assert sec["gemini_api_key"] == "AIzaSyA_test_key_gemini"


def test_config_store_session_records_and_diffs(tmp_path: Path):
    state_file = tmp_path / "hub_state.json"
    store = ConfigStore(state_path=state_file)

    session = SessionRecord(
        task_id="task_abc123",
        repo="my-org/backend-repo",
        title="Fix n+1 query",
        prompt="Optimize queries in user service",
        persona="bolt",
        status=TaskStatus.PASSED,
        branch="curator/bolt-test",
        worktree_path=str(tmp_path / "wt1"),
        diff="--- a/user.py\n+++ b/user.py\n@@ -1 +1 @@\n-old\n+new",
        created_at="2026-11-02T12:00:00Z",
    )
    store.upsert_session(session)

    # Retrieve session
    fetched = store.get_session("task_abc123")
    assert fetched is not None
    assert fetched.title == "Fix n+1 query"
    assert fetched.status == TaskStatus.PASSED

    # List sessions with filter
    all_sessions = store.list_sessions()
    assert len(all_sessions) == 1

    repo_sessions = store.list_sessions(repo="backend-repo")
    assert len(repo_sessions) == 1

    diff = store.get_task_diff("task_abc123")
    assert diff is not None
    assert "+new" in diff


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

    with patch.object(os, "replace", side_effect=OSError("Disk full")):
        with pytest.raises(OSError):
            store.save_config(HubConfig())

    tmp_files = list(tmp_path.glob(".*.tmp")) + list(tmp_path.glob("*.tmp"))
    assert len(tmp_files) == 0


def test_git_commit_authoring_normalization():
    cs_str = CommunitySettings(git_commit_authoring="jules_only")
    assert cs_str.git_commit_authoring == GitAuthoringMode.JULIUS_ONLY
    assert cs_str.git_commit_authoring == "julius_only"

    cs_enum = CommunitySettings(git_commit_authoring=GitAuthoringMode.JULES_ONLY)
    assert cs_enum.git_commit_authoring == GitAuthoringMode.JULIUS_ONLY

    cfg = HubConfig(settings={"git_commit_authoring": "jules_only"})
    assert cfg.settings.git_commit_authoring == GitAuthoringMode.JULIUS_ONLY
    assert cfg.settings.git_commit_authoring == "julius_only"


def test_config_store_data_dir_env_precedence(tmp_path: Path):
    julius_dir = tmp_path / "julius_data"
    jules_dir = tmp_path / "jules_data"

    with patch.dict(os.environ, {"JULIUS_DATA_DIR": str(julius_dir), "JULES_DATA_DIR": str(jules_dir)}):
        store = ConfigStore()
        assert store.config_path.parent == julius_dir.resolve()

    with patch.dict(os.environ, {"JULIUS_DATA_DIR": "", "JULES_DATA_DIR": str(jules_dir)}):
        store = ConfigStore()
        assert store.config_path.parent == jules_dir.resolve()

    with patch.dict(os.environ):
        os.environ.pop("JULIUS_DATA_DIR", None)
        os.environ.pop("JULES_DATA_DIR", None)
        store = ConfigStore()
        assert store.config_path.parent == (Path.cwd() / "data").resolve()
