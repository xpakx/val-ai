import msgspec


class Config(msgspec.Struct, rename="camel"):
    api_key: str
    provider: str
    model: str


def load_config(filename: str) -> Config:
    with open(filename, 'r') as file:
        data = file.read()
    try:
        config = msgspec.json.decode(data, type=Config)
        return config
    except msgspec.DecodeError as e:
        raise Exception(f"decode error: {e}")


def main():
    print("Hello from val-ai!")
    config = load_config("data/config.json")
    print(config)


if __name__ == "__main__":
    main()
