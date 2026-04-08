import msgspec
# TODO: openai uses pydantic, so we might want
# to switch to direct calls
import openai
from typing import TypedDict, Literal


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


Role = Literal["system", "user", "assistant"]


class ChatMessage(TypedDict):
    role: Role
    content: str


class Client:
    def __init__(self, config: Config):
        self.model = config.model
        self.client = openai.OpenAI(
                api_key=config.api_key,
                base_url=config.provider
        )

    def ask(self, messages: list[ChatMessage]):
        response = self.client.chat.completions.create(
                model=self.model,
                # TODO: we don't want to adhere to openai
                # types, as most models ignore those anyway
                # and we will probably migrate to direct
                # HTTP calls anyway
                # pyrefly: ignore [bad-argument-type]
                messages=messages
        )
        content = response.choices[0].message.content
        return content


def main():
    print("Hello from VAL-ai!")
    config = load_config("data/config.json")
    client = Client(config)
    print(client.ask([{"role": "user", "content": "Hello!"}]))


if __name__ == "__main__":
    main()
