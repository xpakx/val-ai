from agent.prompt import PromptPart
from agent.client import ChatMessage, Role
import uuid
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class ContextMessage:
    author: Role
    msg: PromptPart | str
    hidden: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def as_msg(self) -> ChatMessage:
        if isinstance(self.msg, str):
            msg = self.msg
        else:
            msg = self.msg.content()
        return {'role': self.author, 'content': msg}


# TODO: save_context and restore_context
# TODO: git-like tree of messages
class Context:
    def __init__(self):
        self.messages: list[ContextMessage] = []
        self.msg_by_id: dict[str, ContextMessage] = {}
        self.reset_point = 0

    def push(self, author: Role, msg: PromptPart | str) -> ContextMessage:
        new_msg = ContextMessage(
                    author=author,
                    msg=msg,
        )
        self.messages.append(new_msg)
        self.msg_by_id[new_msg.id] = new_msg
        return new_msg

    def get_messages(self) -> list[ChatMessage]:
        return [x.as_msg() for x in self.messages if not x.hidden]

    def hide_message(self, id: str) -> None:
        if id not in self.msg_by_id:
            return
        self.msg_by_id[id].hidden = True

    def show_message(self, id: str) -> None:
        if id not in self.msg_by_id:
            return
        self.msg_by_id[id].hidden = False

    def freeze(self) -> None:
        self.reset_point = len(self.messages)

    def reset(self) -> None:
        if self.reset_point <= 0:
            return
        self.messages = self.messages[0:self.reset_point]
        self.msg_by_id = {}
        for msg in self.messages:
            self.msg_by_id[msg.id] = msg


if __name__ == "__main__":
    ctx = Context()
    ctx.push("user", "test")
    ctx.freeze()
    msg = ctx.push("user", "test2")
    ctx.hide_message(msg.id)
    print(ctx.get_messages())
    ctx.show_message(msg.id)
    print(ctx.get_messages())
    ctx.reset()
    print(ctx.get_messages())
