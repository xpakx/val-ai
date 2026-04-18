import inspect


class SkillDescription:
    def __init__(self, target_class: type):
        self.target_class = target_class
        self.class_name = target_class.__name__
        self._content = None

    def _format_type(self, annotation) -> str:
        if annotation is inspect.Parameter.empty:
            return "Any"
        if isinstance(annotation, str):
            return annotation
        if hasattr(annotation, "__name__"):
            return annotation.__name__
        return str(annotation).replace("typing.", "")

    def _get_docstring_description(self, docstring: str) -> str:
        if not docstring:
            return "No description provided."
        lines = [line.strip() for line in docstring.split('\n') if line.strip()]
        return lines[0] if lines else "No description provided."

    def content(self) -> str:
        if self._content:
            return self._content
        return self.generate_markdown()

    def generate_markdown(self) -> str:
        class_doc = inspect.getdoc(self.target_class) or "No class description."
        md_output = [
            f"# AI Skill: {self.class_name}",
            "",
            "## Description",
            f"{class_doc}",
            "",
            "## Capability Manifest",
            "The following functions are available for the agent to execute.",
            ""
        ]

        for name, method in inspect.getmembers(
                self.target_class, predicate=inspect.isfunction):
            if name.startswith("_"):
                continue

            sig = inspect.signature(method)
            doc = inspect.getdoc(method)
            desc = self._get_docstring_description(doc)

            md_output.append(f"### `{name}`")
            md_output.append(f"**Purpose**: {desc}\n")

            md_output.append("**Parameters**:")
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue

                type_str = self._format_type(param.annotation)
                default_str = ""
                if param.default is not inspect.Parameter.empty:
                    default_str = f", Default: `{param.default}`"
                else:
                    default_str = ", **Required**"

                md_output.append(f"- `{param_name}` ({type_str}){default_str}")

            if len(sig.parameters) <= 1:
                md_output.append("- None")

            md_output.append("")

            return_type = self._format_type(sig.return_annotation)
            md_output.append(f"**Returns**: `{return_type}`")
            md_output.append("\n---\n")

        return "\n".join(md_output)

    def save_to_file(self, filename: str = "SKILL.md"):
        content = self.content()
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ Successfully generated {filename} for class '{self.class_name}'")
