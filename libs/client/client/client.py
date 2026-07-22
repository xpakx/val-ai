import time
from collections.abc import Callable
from typing import Any, Literal, TypeVar

import msgspec
import requests

from client.config import Config
from client.format import prepare_response_format
from client.fibonacci import backoff_retry
from client.json import JsonRescuer
from client.typedefs import (
    ChatMessage,
    GoogleErrorWrapper,
    Message,
    OpenAIResponse,
    OpenAIResponseFormat,
    OpenAIToolCall,
    TextMessage,
    ToolCallGen,
)

T = TypeVar("T")


class Client:
    def __init__(self, config: Config, backoff: Callable | None = None):
        self.config = config
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.api_key}",
        }
        self.backoff = backoff
        self._temperature = 0.7
        self._rescuer = JsonRescuer()

    def set_temperature(self, temp: float) -> None:
        self._temperature = max(0.0, min(1.0, temp))

    def set_backoff(self, backoff: Callable) -> None:
        self.backoff = backoff

    def unset_backoff(self) -> None:
        self.backoff = None

    def completion_url(self) -> str:
        return f"{self.config.provider}chat/completions"

    def request(self, payload):
        return requests.post(self.completion_url(), headers=self.headers, json=payload)

    # TODO: 429 error
    def call_backoff(self, payload: dict[str, Any]) -> requests.Response | None:
        if not self.backoff:
            return None
        result = backoff_retry(
                task=lambda: self.request(payload),
                delays=self.backoff(),
                max_attempts=5,
        )
        if result.status_code == 429:
            err = msgspec.json.decode(result.text, type=list[GoogleErrorWrapper])[0]
            print(err)
            details = err.error.details
            delay = None
            for d in details:
                if d.retryDelay:
                    delay = d.retryDelay
                    break
            print(delay)
            # TODO: other providers
            # TODO: google info about delay very often is wrong
            # TODO: sometimes time could prolly be longer than 59s
            delay = int(delay[:-1])
            time.sleep(delay)
            return self.call_backoff(payload)
        else:
            return result

    def call_api(
        self,
        messages: list[ChatMessage],
        tools: list[ToolCallGen] | None = None,
        tool_choice: Literal["auto", "none", "required"] | None = None,
        response_format: OpenAIResponseFormat | type[msgspec.Struct] | None = None,
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
        if response_format:
            if isinstance(response_format, OpenAIResponseFormat):
                payload["response_format"] = msgspec.to_builtins(response_format)
            else:
                payload["response_format"] = msgspec.to_builtins(
                    prepare_response_format(response_format)
                )

        if self.backoff:
            response = self.call_backoff(payload)
        else:
            response = requests.post(
                self.completion_url(), headers=self.headers, json=payload
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
        return self._decode(content, list[Message])

    def ask_typed(self, messages: list[ChatMessage], target: type[T]) -> T:
        response = self.call_api(messages)
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Couldn't parse")
        return self._decode(content, target)

    def ask_with_tools(
        self,
        messages: list[ChatMessage],
        tools: list[ToolCallGen] | None = None,
        tool_choice: Literal["auto", "none", "required"] | None = None,
    ) -> tuple[list[TextMessage], list[OpenAIToolCall]]:
        response = self.call_api(messages, tools, tool_choice)
        content = response.choices[0].message.content
        tool_calls = response.choices[0].message.tool_calls or []
        if not content:
            return [], tool_calls
        return self._decode(content, list[TextMessage]), tool_calls

    def _decode(self, text: str, target_type: type[T]) -> T:
        print(text)
        try:
            return msgspec.json.decode(text, type=target_type)
        except Exception:
            new_text = self._rescuer._rescue_imperfect_json(text, target_type)
            print(new_text)
            return new_text
