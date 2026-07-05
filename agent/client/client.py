import msgspec
from typing import Literal, Callable, Any
from agent.config import Config
from agent.client.typedefs import (
        ChatMessage, OpenAIResponse,
        Message, TextMessage, OpenAIToolCall
)
from agent.toolgen import ToolCall
import requests


class Client:
    def __init__(self, config: Config, backoff: Callable | None = None):
        self.config = config
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.api_key}"
        }
        self.backoff = backoff
        self._temperature = 0.7
        self._native_tools_enabled = False

    def set_temperature(self, temp: float) -> None:
        self._temperature = max(0.0, min(1.0, temp))

    def set_backoff(self, backoff: Callable) -> None:
        self.backoff = backoff

    def unset_backoff(self) -> None:
        self.backoff = None

    def completion_url(self) -> str:
        return f'{self.config.provider}chat/completions'

    def call_backoff(
            self, payload: dict[str, Any]) -> requests.Response | None:
        if not self.backoff:
            return None
        return self.backoff(
                lambda: requests.post(
                        self.completion_url(),
                        headers=self.headers,
                        json=payload
                ),
                5
        )

    def call_api(
            self,
            messages: list[ChatMessage],
            tools: list[ToolCall] | None = None,
            tool_choice: Literal['auto', 'none', 'required'] | None = None,
            ) -> OpenAIResponse:
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self._temperature,
        }

        if tools:
            payload["tools"] = msgspec.to_builtins(tools)
        if tool_choice:
            payload["tool_choice"] = tool_choice

        if self.backoff:
            response = self.call_backoff(payload)
        else:
            response = requests.post(
                self.completion_url(),
                headers=self.headers,
                json=payload
            )

        if response is None:
            print("Error: no response")
            raise Exception()
        print(response.text)

        if not response:
            print(f"Error: {response.status_code} error:")
            print(response.text)
            raise Exception()

        print(response.text)
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
        if not content:
            return []
        return self._decode(content)

    def ask_with_tools(
        self,
        messages: list[ChatMessage],
        tools: list[ToolCall] | None = None,
        tool_choice: Literal['auto', 'none', 'required'] | None = None,
    ) -> tuple[list[Message], list[OpenAIToolCall]]:
        response = self.call_api(messages, tools, tool_choice)
        content = response.choices[0].message.content
        tool_calls = response.choices[0].message.tool_calls or []
        if not content:
            return [], tool_calls
        return self._decode(content), tool_calls

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
