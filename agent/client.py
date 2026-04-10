import msgspec
from typing import TypedDict, Literal, Type
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
        return self._decode(content, type=list[Message])

    def _decode(self, text: str, type: Type) -> list:
        print(text)
        try:
            return msgspec.json.decode(text, type=type)
        except Exception as e:
            new_text = self._rescue_imperfect_json(text)
            if not new_text:
                raise e
            print(new_text)
            return msgspec.json.decode(new_text, type=type)

    def _rescue_imperfect_json(self, text: str) -> str | None:
        print("rescuing json")
        start_index = text.find('[')
        if start_index == -1:
            return None

        counter = 0
        for i in range(start_index, len(text)):
            if text[i] == '[':
                counter += 1
            elif text[i] == ']':
                counter -= 1
            if counter == 0:
                return text[start_index:i+1]
        return None
