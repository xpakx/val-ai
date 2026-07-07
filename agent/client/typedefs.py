from typing import TypedDict, Literal
import msgspec
from agent.toolgen import Parameters

Role = Literal["system", "user", "assistant", "tool"]


class ChatTextMessage(TypedDict):
    role: Role
    content: str


class ToolResponse(TypedDict):
    role: Role
    tool_call_id: str
    name: str
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


class OpenAIFunc(msgspec.Struct):
    arguments: str
    name: str


class OpenAIToolCall(msgspec.Struct):
    extra_content: dict[str, dict[str, str]]  # TODO: prolly a bad idea
    function: OpenAIFunc
    id: str
    type: Literal["function"] = "function"


class OpenAIMessage(msgspec.Struct):
    content: str | None = None
    tool_calls: list[OpenAIToolCall] | None = None


class OpenAIChoice(msgspec.Struct):
    finish_reason: Literal["stop", "tool_calls"]
    index: int
    message: OpenAIMessage


class OpenAIResponse(msgspec.Struct):
    choices: list[OpenAIChoice]


class ToolCallMessage(TypedDict):
    role: Role
    tool_calls: list[OpenAIToolCall]


class OpenAIResponseSchema(msgspec.Struct):
    name: str
    schema: Parameters
    strict: bool = True


class OpenAIResponseFormat(msgspec.Struct):
    json_schema: OpenAIResponseSchema
    type: Literal["json_schema"] = "json_schema"


ChatMessage = ChatTextMessage | ToolResponse | ToolCallMessage
