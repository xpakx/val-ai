from typing import Protocol, Any


class PromptPart(Protocol):
    dirty: bool
    def content(self) -> str: ...
    def update(self, context: dict[str, Any]) -> None: ...


class Prompt:
    def __init__(self, message: str):
        self._text = message
        self.parts: list[PromptPart] = []
        self.dirty = True
        self._content = ""

    def add_part(self, part: PromptPart):
        self.parts.append(part)
        self.dirty = True

    def update(self, context: dict[str, Any]) -> None:
        for part in self.parts:
            part.update(context)
            if part.dirty:
                self.dirty = True

    def content(self) -> str:
        if self.dirty:
            self._content = self.generate()
            self.dirty = False
        return self._content

    def generate(self) -> str:
        content = self._text

        for part in self.parts:
            part_value = part.content()
            if part_value:
                content += part_value
                content += '\n'
        return content
