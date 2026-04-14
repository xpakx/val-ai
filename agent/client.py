import msgspec
from typing import TypedDict, Literal, Callable, Any
from agent.config import Config
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


# TODO: native tool call if model supports them
class Client:
    def __init__(self, config: Config, backoff: Callable | None = None):
        self.config = config
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.api_key}"
        }
        self.backoff = backoff

    def set_backoff(self, backoff: Callable):
        self.backoff = backoff

    def unset_backoff(self):
        self.backoff = None

    def call_backoff(
            self, payload: dict[str, Any]) -> requests.Response | None:
        if not self.backoff:
            return None
        return self.backoff(
                lambda: requests.post(
                        f'{self.config.provider}chat/completions',
                        headers=self.headers,
                        json=payload
                ),
                5
        )

    def call_api(self, messages: list[ChatMessage]) -> OpenAIResponse:
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": 0.7
        }

        if self.backoff:
            response = self.call_backoff(payload)
        else:
            response = requests.post(
                f'{self.config.provider}chat/completions',
                headers=self.headers,
                json=payload
            )

        if not response:
            print("Error: no response")
            print(response.status_code)
            print(response.text)
            raise Exception()

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
        return self._decode(content)

    def _decode(self, text: str) -> list[Message]:
        print(text)
        try:
            return msgspec.json.decode(text, type=list[Message])
        except Exception:
            new_text = self._rescue_imperfect_json(text)
            print(new_text)
            return new_text

    def _rescue_imperfect_json(self, text: str) -> list[Message]:
        # TODO: we should probably found all potential
        # candidates and check whether they are proper
        # json
        new_text = self._find_json(text)
        if new_text:
            return msgspec.json.decode(new_text, type=list[Message])
        new_text = self._find_json(text, start_symbol='{')
        if new_text:
            return [msgspec.json.decode(new_text, type=Message)]
        return [TextMessage(text)]

    def _is_valid_json(self, text: str) -> bool:
        try:
            msgspec.json.decode(text, type=msgspec.Raw)
            return True
        except msgspec.DecodeError:
            return False

    def _find_json(
            self,
            text: str,
            start_symbol: Literal['[', '{'] = '['
    ) -> str | None:
        print("rescuing json")
        end_symbol = ']' if start_symbol == '[' else '}'
        start_index = text.find(start_symbol)
        if start_index == -1:
            return None

        counter = 0
        for i in range(start_index, len(text)):
            if text[i] == start_symbol:
                counter += 1
            elif text[i] == end_symbol:
                counter -= 1
            if counter == 0:
                potential_text = text[start_index:i+1]
                if self._is_valid_json(potential_text):
                    return potential_text
        return None
