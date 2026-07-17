import inspect
from typing import Callable, Any, cast
from dataclasses import dataclass
import msgspec

from promptmachine import Prompt
from client.typedefs import (
        FunctionDefinition,
        PropertyType,
        ToolCallGen,
        Parameters,
        Property
)


class ToolDescription(Prompt):
    def __init__(self, target_function: Callable):
        self.target_function = target_function
        self.func_name = target_function.__name__
        self._content = ""
        self.dirty = True
        self.parent = None
        self._show = True
        self._args_struct = self.prepare_args()

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

    def _type_for_call(self, tp: str) -> PropertyType:
        if tp == 'str':
            return 'string'
        if tp == 'int':
            return 'integer'
        if tp == 'float':
            return 'number'
        if tp == 'bool':
            return 'boolean'
        return 'null'

    def generate_call(self) -> ToolCallGen:
        func_doc = inspect.getdoc(self.target_function)
        if (not func_doc):
            raise Exception('Tool does not have description')

        sig = inspect.signature(self.target_function)

        properties = {}
        required = []

        if sig.parameters:
            for param_name, param in sig.parameters.items():
                type_str = self._format_type(param.annotation)
                print(type_str)
                properties[param_name] = Property(
                        type=self._type_for_call(type_str)
                )

                if param.default is inspect.Parameter.empty:
                    required.append(param_name)
        params = Parameters(
                properties=properties,
        )
        if required:
            params.required = required
        definition = FunctionDefinition(
                name=self.func_name,
                description=func_doc,
                parameters=params,
        )
        return ToolCallGen(function=definition)

    def parse_args(self, data: str):
        return msgspec.to_builtins(
            msgspec.json.decode(data, type=self._args_struct)
        )

    def prepare_args(self) -> msgspec.Struct:
        sig = inspect.signature(self.target_function)
        fields = {}
        if sig.parameters:
            for param_name, param in sig.parameters.items():
                fields[param_name] = param.annotation
        return cast(
                msgspec.Struct,
                msgspec.defstruct(
                    self.func_name,
                    fields,
                    frozen=True
                )
        )


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
            function=func
    )
