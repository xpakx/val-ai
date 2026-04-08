# TODO: openai uses pydantic, so we might want
# to switch to direct calls
import openai
from typing import TypedDict, Literal
from config import Config


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
