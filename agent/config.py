import msgspec
from pathlib import Path


class Config(msgspec.Struct, rename="camel"):
    api_key: str
    provider: str
    model: str


def load_config(filename: str | Path | None) -> Config:
    if filename:
        return load_config_from_file(filename)

    return load_config_from_file('./val.config.json')
    # TODO: XDG


def load_config_from_file(filename: str | Path) -> Config:
    filepath = Path(filename)
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
