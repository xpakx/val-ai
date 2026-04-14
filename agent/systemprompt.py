import inspect
from typing import Callable, Any


class SystemPromptInformation:
    def __init__(self, target_function: Callable):
        self.target_function = target_function
        self._description = None
        self.dirty = False
        self.parent = None

    def content(self) -> str:
        if not self._description:
            self.generate()
        return self._do_generate()

    def update(self, context: dict[str, Any]) -> None:
        pass

    def _do_generate(self) -> str:
        desc = self._description or ''
        func_result = self.target_function()
        return f"{desc}: {func_result}"

    def _get_docstring_description(self, docstring: str) -> str | None:
        lines = [
                line.strip() for line in docstring.split('\n') if line.strip()
        ]
        return lines[0] if lines else None

    def generate(self) -> None:
        func_doc = inspect.getdoc(self.target_function)
        if (not func_doc):
            raise Exception('Prompt provider does not have description')
        self._description = func_doc

    def make_dirty(self) -> None:
        self.dirty = True
        if self.parent:
            self.parent.make_dirty()


def get_system_prompt_info(func: Callable) -> SystemPromptInformation:
    return SystemPromptInformation(func)
