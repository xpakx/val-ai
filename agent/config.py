import msgspec
import os
from pathlib import Path


class Config(msgspec.Struct, rename="camel"):
    api_key: str
    provider: str
    model: str


def load_config(filename: str | Path | None) -> Config:
    if filename:
        filepath = Path(filename)
        return load_config_from_file(filepath)

    local_config = Path('./valconfig.json')
    if local_config.is_file():
        return load_config_from_file(local_config)

    config_dir = get_xdg_config_location()
    config_file = config_dir / 'val/config.json'
    if local_config.is_file():
        return load_config_from_file(config_file)

    raise Exception("Couldn't find config file")


def load_config_from_file(filepath:  Path) -> Config:
    if not filepath.is_file():
        raise FileNotFoundError()
    data = filepath.read_text()
    if not data:
        raise Exception("Couldn't read file")
    try:
        config = msgspec.json.decode(data, type=Config)
        return config
    except msgspec.DecodeError as e:
        raise Exception(f"decode error: {e}")


def get_xdg(var: str, default: str) -> Path:
    path_str = os.environ.get(var)
    if path_str:
        path_str = Path(path_str)
    else:
        home = os.environ.get('HOME', '')
        path_str = Path(home) / default
    path = path_str / 'subsplease'
    return path


def get_xdg_config_location() -> Path:
    return get_xdg('XDG_CONFIG_HOME', '.config')
