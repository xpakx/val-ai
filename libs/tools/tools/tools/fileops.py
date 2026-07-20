from pathlib import Path
from tools.toolgen import get_tool, ToolDefinition


class FileTool:
    def __init__(self, base_path: str | Path = '.'):
        self.root = Path(base_path).resolve()

    def read(self) -> ToolDefinition:
        func = self.read_file
        return get_tool(func)

    def write(self) -> ToolDefinition:
        func = self.write_file
        return get_tool(func)

    def ls(self) -> ToolDefinition:
        func = self.list_files
        return get_tool(func)

    def glob(self) -> ToolDefinition:
        func = self.glob_files
        return get_tool(func)

    def tools(self) -> list[ToolDefinition]:
        return [
                self.read(),
                self.write(),
                self.ls(),
                self.glob(),
        ]

    def get_safe_path(self, path: str | None) -> Path:
        if path is None:
            path = "."

        requested_path = Path(path)

        if requested_path.is_absolute():
            requested_path = Path("./" + path.lstrip('/'))

        requested_path = (self.root / requested_path).resolve()

        if not requested_path.is_relative_to(self.root):
            raise ValueError(f"Access denied: Path '{path}' is outside the working directory.")

        return requested_path

    def read_file(self, path: str):
        """
        Reads the file on filesystem in a folder agent runs in
        """
        try:
            file_path = self.get_safe_path(path)
        except ValueError as e:
            return f"Error: {e}"

        if not file_path.exists():
            return "Error: File does not exist"
        if file_path.is_dir():
            return "Error: File is a directory"
        try:
            return file_path.read_text()
        except Exception:
            return "Error: Couldn't read the file!"

    def list_files(self, path: str | None = None):
        """
        List files and directories at a given path.
        If no path is provided, lists files in the current
        directory.
        """
        try:
            dir_path = self.get_safe_path(path)
        except ValueError as e:
            return f"Error: {e}"

        if not dir_path.is_dir():
            return "Error: File is not a directory"

        files = [(f'{f.name}/' if f.is_dir() else f.name) for f in dir_path.iterdir()]
        return "\n".join(files)

    def update_file(self, path: Path, old_str: str, new_str: str) -> str:
        if path.is_dir():
            return "Error: File is a directory"

        content = path.read_text()
        if old_str in content:
            new_content = content.replace(old_str, new_str, 1)
            path.write_text(new_content)
        else:
            return "Error: old_str not found; skipping write."
        return "Change applied."

    def create_file(self, path: Path, new_str: str) -> str:
        path.write_text(new_str)
        return "Change applied."

    def write_file(self, path: str, old_str: str, new_str: str) -> str:
        """
        Changes first occurence of old_str to new_str
        in a file on filesystem in a folder agent runs in.
        if file does not exist, creates it
        """
        try:
            file_path = self.get_safe_path(path)
        except ValueError as e:
            return f"Error: {e}"

        try:
            if file_path.exists():
                return self.update_file(file_path, old_str, new_str)
            else:
                return self.create_file(file_path, new_str)
        except Exception:
            return "Error: Couldn't write to file!"

    def glob_files(self, pattern: str, path: str | None = None) -> str:
        """
        Searches for files and directories matching a glob pattern.
        If no path is provided, searches from the current directory.
        Supports recursive search using '**' (e.g., '**/*.py').
        """
        try:
            dir_path = self.get_safe_path(path)
        except ValueError as e:
            return f"Error: {e}"

        if not dir_path.is_dir():
            return "Error: Base path is not a directory"

        try:
            files = []
            max_results = 20

            for i, f in enumerate(dir_path.glob(pattern)):
                if i >= max_results:
                    files.append(f"... [Truncated after {max_results} results]")
                    break
                rel_path = f.relative_to(dir_path)
                files.append(f"{rel_path}/" if f.is_dir() else str(rel_path))
            if not files:
                return "No files found matching the pattern."
            return "\n".join(files)
        except Exception as e:
            return f"Error: Couldn't execute glob search! {e}"
