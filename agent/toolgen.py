import inspect
from typing import Callable, Any
from dataclasses import dataclass


class ToolDescription:
    def __init__(self, target_function: Callable):
        self.target_function = target_function
        self.func_name = target_function.__name__
        self._content = None
        self.dirty = True

    def _format_type(self, annotation) -> str:
        if annotation is inspect.Parameter.empty:
            return "Any"
        if isinstance(annotation, str):
            return annotation
        if hasattr(annotation, "__name__"):
            return annotation.__name__
        return str(annotation).replace("typing.", "")

    def _get_docstring_description(self, docstring: str) -> str | None:
        lines = [
                line.strip() for line in docstring.split('\n') if line.strip()
        ]
        return lines[0] if lines else None

    def update(self, context: dict[str, Any]) -> None:
        pass

    def content(self) -> str:
        if self._content:
            return self._content
        return self.generate()

    def generate(self) -> str:
        func_doc = inspect.getdoc(self.target_function)
        if (not func_doc):
            raise Exception('Tool does not have description')
        short_desc = self._get_docstring_description(func_doc)
        if (not short_desc):
            raise Exception('Tool does not have description')

        sig = inspect.signature(self.target_function)

        output = [
            f"name: {self.func_name}",
            f"description: {func_doc}",
            "parameters:"
        ]

        if not sig.parameters:
            output.append("- None")
        else:
            for param_name, param in sig.parameters.items():
                type_str = self._format_type(param.annotation)

                if param.default is not inspect.Parameter.empty:
                    default_str = f", default: `{param.default}`"
                else:
                    default_str = ''
                output.append(f"- `{param_name}` ({type_str}){default_str}")

        return "\n".join(output)


@dataclass
class ToolDefinition:
    name: str
    description: ToolDescription
    function: Callable


def get_tool(func: Callable) -> ToolDefinition:
    desc = ToolDescription(func)
    return ToolDefinition(
            name=desc.func_name,
            description=desc,
            function=func,
    )
