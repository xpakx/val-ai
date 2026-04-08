import msgspec
from typing import TypedDict, Literal
from config import Config
import requests


Role = Literal["system", "user", "assistant"]


class ChatMessage(TypedDict):
    role: Role
    content: str


class Base(msgspec.Struct, tag_field="type"):
    pass


class TextMessage(Base, tag="text"):
    type = "text"
    text: str


class ToolCall(Base, tag="tool"):
    type = "tool"
    name: str
    args: dict[str, str]


Message = TextMessage | ToolCall


class OpenAIMessage(msgspec.Struct):
    content: str


class OpenAIChoice(msgspec.Struct):
    message: OpenAIMessage


class OpenAIResponse(msgspec.Struct):
    choices: list[OpenAIChoice]


class Client:
    def __init__(self, config: Config):
        self.config = config
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.api_key}"
        }

    def call_api(self, messages: list[ChatMessage]) -> OpenAIResponse:
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": 0.7
        }

        response = requests.post(
                f'{self.config.provider}chat/completions',
                headers=self.headers,
                json=payload
        )

        if response.status_code == 200:
            print(response.text)
            return msgspec.json.decode(response.text, type=OpenAIResponse)
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            raise Exception()

    def ask(self, messages: list[ChatMessage]) -> list[Message]:
        response = self.call_api(messages)
        print(response)
        content = response.choices[0].message.content
        print(content)
        return msgspec.json.decode(content, type=list[Message])
