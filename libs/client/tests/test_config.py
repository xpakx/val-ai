import os
from unittest.mock import patch

import msgspec
import pytest
from client.config import (
    Config,
    RawConfig,
    finalize_config,
    overwrite_from_env,
)


@pytest.fixture
def mock_env():
    with patch.dict(os.environ, {}, clear=True):
        yield


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
