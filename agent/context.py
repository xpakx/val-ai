from agent.prompt import PromptPart
from agent.client import ChatMessage, Role
import uuid
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class ContextMessage:
    author: Role
    msg: PromptPart | str
    timestamp: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def as_msg(self) -> ChatMessage:
        if isinstance(self.msg, str):
            msg = self.msg
        else:
            msg = self.msg.content()
        return {'role': self.author, 'content': msg}


class Context:
    def __init__(self):
        self.messages: list[ContextMessage] = []

    def push(self, author: Role, msg: PromptPart | str) -> None:
        self.messages.append(
                ContextMessage(
                    author=author,
                    msg=msg,
                )
        )

    def get_messages(self) -> list[ChatMessage]:
        return [x.as_msg() for x in self.messages]


if __name__ == "__main__":
    ctx = Context()
    ctx.push("user", "test")
    print(ctx.get_messages())
