import os
from pathlib import Path
from unittest.mock import patch

import msgspec
import pytest
from client.config import (
    Config,
    RawConfig,
    check_files,
    finalize_config,
    get_xdg,
    get_xdg_config_location,
    get_xdg_data_location,
    load_config_from_file,
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


@pytest.fixture
def mock_cwd(tmp_path):
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(original_cwd)


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


# reading config from file
def test_load_config_from_file_success(tmp_path):
    conf_file = tmp_path / "test.json"
    conf_file.write_text('{"apiKey": "abc", "provider": "xyz", "model": "123"}')
    raw = load_config_from_file(conf_file)
    assert raw.api_key == "abc"
    assert raw.provider == "xyz"
    assert raw.model == "123"


def test_load_config_from_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_config_from_file(Path("does_not_exist.json"))


def test_load_config_from_file_empty(tmp_path):
    empty_file = tmp_path / "empty.json"
    empty_file.touch()
    with pytest.raises(Exception, match="Couldn't read file"):
        load_config_from_file(empty_file)


def test_load_config_from_file_invalid_json(tmp_path):
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("broken json")
    with pytest.raises(Exception, match="decode error:"):
        load_config_from_file(bad_file)


def test_check_files_explicit_filename(tmp_path):
    explicit_file = tmp_path / "explicit.json"
    explicit_file.write_text('{"provider": "explicit"}')

    result = check_files(explicit_file)
    assert result.provider == "explicit"


def test_check_files_local_fallback(mock_cwd):
    local_file = mock_cwd / "valconfig.json"
    local_file.write_text('{"provider": "local"}')

    result = check_files(None)
    assert result.provider == "local"


def test_check_files_xdg_fallback(mock_env, mock_cwd, mock_home):
    xdg_config_dir = mock_home / ".config"

    with patch.dict(os.environ, {"XDG_CONFIG_HOME": str(xdg_config_dir)}):
        config_file = xdg_config_dir / "val" / "config.json"
        config_file.parent.mkdir(parents=True)
        config_file.write_text('{"provider": "xdg"}')

        result = check_files(None)

    assert result.provider == "xdg"


def test_check_files_no_files_found(mock_env, mock_cwd, mock_home):
    result = check_files(None)

    assert result.api_key is None
    assert result.provider is None
    assert result.model is None
