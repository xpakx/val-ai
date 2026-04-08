import msgspec
# TODO: openai uses pydantic, so we might want
# to switch to direct calls
import openai


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


class Client:
    def __init__(self, config: Config):
        self.model = config.model
        self.client = openai.OpenAI(
                api_key=config.api_key,
                base_url=config.provider
        )

    def ask(self, messages: list[dict[str, str]]):
        response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
        )
        content = response.choices[0].message.content
        return content


def main():
    print("Hello from val-ai!")
    config = load_config("data/config.json")
    client = Client(config)
    print(client.ask([{"role": "user", "content": "Hello!"}]))


if __name__ == "__main__":
    main()
