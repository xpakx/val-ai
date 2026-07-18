import os
from unittest.mock import patch
from pathlib import Path
import msgspec
import pytest
from client.config import (
    Config,
    RawConfig,
    finalize_config,
    get_xdg,
    get_xdg_config_location,
    get_xdg_data_location,
    overwrite_from_env,
)


@pytest.fixture
def mock_env():
    with patch.dict(os.environ, {}, clear=True):
        yield


@pytest.fixture
def mock_home(tmp_path):
    home_dir = tmp_path / "mock_home"
    home_dir.mkdir()
    with patch.object(Path, "home", return_value=home_dir):
        yield home_dir


def test_overwrite_from_env(mock_env):
    cfg = RawConfig(api_key=None, provider="default", model=None)
    original_cfg = msgspec.structs.replace(cfg)

    with patch.dict(os.environ, {"VAL_API_KEY": "secret123", "VAL_MODEL": "gpt-4"}):
        overwrite_from_env(cfg)

    assert cfg.api_key == "secret123"
    assert cfg.model == "gpt-4"

    assert cfg.provider == original_cfg.provider
    assert original_cfg.api_key is None
    assert original_cfg.model is None


# finalize
def test_finalize_config_success():
    raw = RawConfig(api_key="123", provider="openai", model="gpt-4")
    config = finalize_config(raw)

    assert isinstance(config, Config)
    assert config.api_key == "123"
    assert config.provider == "openai"
    assert config.model == "gpt-4"


def test_finalize_config_missing_fields_raises():
    raw = RawConfig(api_key="123")
    with pytest.raises(msgspec.ValidationError):
        finalize_config(raw)


# paths
def test_get_xdg_with_env(mock_env, tmp_path):
    custom_path = tmp_path / "custom"

    with patch.dict(os.environ, {"MY_VAR": str(custom_path)}):
        result = get_xdg("MY_VAR", ".default")

    assert result == custom_path


def test_get_xdg_without_env(mock_env, mock_home):
    result = get_xdg("MY_VAR", ".default")
    assert result == mock_home / ".default"


def test_get_xdg_config_location(mock_env, mock_home):
    assert get_xdg_config_location() == mock_home / ".config" / "val"


def test_get_xdg_data_location(mock_env, mock_home):
    assert get_xdg_data_location() == mock_home / ".local/share"
