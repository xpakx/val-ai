from typing import Protocol, Any
from agent.signals import Signal, Computed, effect, Effect
from string import Template


class PromptPart(Protocol):
    dirty: bool
    parent: "None | PromptPart"
    def content(self) -> str: ...
    def update(self, context: dict[str, Any]) -> None: ...
    def make_dirty(self) -> None: ...
    def bind_visibility(self, sig: Signal | Computed) -> None: ...


class Prompt:
    def __init__(self, message: str):
        self._text = message
        self.parts: list[PromptPart] = []
        self.dirty = True
        self.parent: None | PromptPart = None
        self._content = ""
        self._show = True
        self._effects: list[Effect] = []

    def add_part(self, part: PromptPart):
        self.parts.append(part)
        part.parent = self
        self.make_dirty()

    def update(self, context: dict[str, Any]) -> None:
        for part in self.parts:
            part.update(context)

    def content(self) -> str:
        if self.dirty:
            self._content = self.generate()
            self.dirty = False
        return self._content

    def generate(self) -> str:
        content = self._text if self._show else ''

        for part in self.parts:
            part_value = part.content()
            if part_value:
                content += part_value
                content += '\n'
        return content

    def make_dirty(self) -> None:
        self.dirty = True
        if self.parent:
            self.parent.make_dirty()

    def set_visibility(self, val: bool) -> None:
        self._show = val
        self.make_dirty()

    def bind_visibility(self, sig: Signal[bool] | Computed[bool]) -> None:
        eff = effect(
                lambda val: self.set_visibility(val),
                [sig]
        )
        self._effects.append(eff)


class TemplatedPrompt(Prompt):
    def __init__(
            self, template: Template, defaults: None | dict[str, Any] = None):
        self._template: Template = template
        self._text = ""
        self.parts: list[PromptPart] = []
        self.dirty = True
        self.template_dirty = True
        self._prepare_defaults(defaults)
        self.parent: None | PromptPart = None
        self._content = ""
        self._show = True
        self._effects: list[Effect] = []

    def generate(self) -> str:
        if self.template_dirty:
            self._text = self.update_template()
        content = self._text if self._show else ''

        for part in self.parts:
            part_value = part.content()
            if part_value:
                content += part_value
                content += '\n'
        return content

    def update_template(self) -> str:
        data = self._defaults | self._values
        text = self._template.substitute(**data)
        self.template_dirty = False
        return text

    def _prepare_defaults(self, defaults: None | dict[str, Any]) -> None:
        self._defaults = {}
        self._values = {}
        t = self._template
        print(t.template)
        placeholders = self._template.get_identifiers()
        print(placeholders)
        for placeholder in placeholders:
            print(placeholder)
            if placeholder in defaults:
                self._defaults[placeholder] = defaults[placeholder]
            else:
                self._defaults[placeholder] = f"${placeholder}"
