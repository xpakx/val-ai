import msgspec
import os
from pathlib import Path


class RawConfig(msgspec.Struct, rename="camel"):
    api_key: str | None = None
    provider: str | None = None
    model: str | None = None


class Config(msgspec.Struct):
    api_key: str
    provider: str
    model: str


def finalize_config(cfg: RawConfig) -> Config:
    return msgspec.convert(msgspec.structs.asdict(cfg), Config)


def load_config(filename: str | Path | None) -> Config:
    conf = check_files(filename)
    # TODO: env variables
    return finalize_config(conf)


def check_files(filename: str | Path | None) -> RawConfig:
    if filename:
        filepath = Path(filename)
        return load_config_from_file(filepath)

    local_config = Path('./valconfig.json')
    if local_config.is_file():
        return load_config_from_file(local_config)

    config_dir = get_xdg_config_location()
    config_file = config_dir / 'config.json'
    if config_file.is_file():
        return load_config_from_file(config_file)
    return RawConfig()


def load_config_from_file(filepath:  Path) -> RawConfig:
    if not filepath.is_file():
        raise FileNotFoundError()
    data = filepath.read_text()
    if not data:
        raise Exception("Couldn't read file")
    try:
        config = msgspec.json.decode(data, type=RawConfig)
        return config
    except msgspec.DecodeError as e:
        raise Exception(f"decode error: {e}")


def get_xdg(var: str, default: str) -> Path:
    path_str = os.environ.get(var)
    if path_str:
        path_str = Path(path_str)
    else:
        path_str = Path.home() / default
    path = path_str / 'val'
    return path


def get_xdg_config_location() -> Path:
    return get_xdg('XDG_CONFIG_HOME', '.config')
