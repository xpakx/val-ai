from pathlib import Path


def get_weather(city: str) -> str:
    """
    Fetches the current weather for a specific city.
    """
    if "london" in city.lower():
        return "15°C and cloudy"
    return "22°C and sunny"


def get_safe_path(
        path: str | None,
        root_dir: str | Path = "."
) -> Path:
    if path is None:
        path = "."

    root = Path(root_dir).resolve()
    requested_path = Path(path)

    if requested_path.is_absolute():
        requested_path = Path("./" + path.lstrip('/'))

    requested_path = (root / requested_path).resolve()

    if not requested_path.is_relative_to(root):
        raise ValueError(f"Access denied: Path '{path}' is outside the working directory.")

    return requested_path


def read_file(path: str):
    """
    Reads the file on filesystem in a folder agent runs in
    """
    try:
        file_path = get_safe_path(path)
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


def list_files(path: str | None = None):
    """
    List files and directories at a given path.
    If no path is provided, lists files in the current
    directory.
    """
    try:
        dir_path = get_safe_path(path)
    except ValueError as e:
        return f"Error: {e}"

    if not dir_path.is_dir():
        return "Error: File is not a directory"

    files = [(f'{f.name}/' if f.is_dir() else f.name) for f in dir_path.iterdir()]
    return "\n".join(files)


def update_file(path: Path, old_str: str, new_str: str) -> str:
    if path.is_dir():
        return "Error: File is a directory"

    content = path.read_text()
    if old_str in content:
        new_content = content.replace(old_str, new_str, 1)
        path.write_text(new_content)
    else:
        return "Error: old_str not found; skipping write."
    return "Change applied."


def create_file(path: Path, new_str: str) -> str:
    path.write_text(new_str)
    return "Change applied."


def write_file(path: str, old_str: str, new_str: str) -> str:
    """
    Changes first occurence of old_str to new_str
    in a file on filesystem in a folder agent runs in.
    if file does not exist, creates it
    """
    try:
        file_path = get_safe_path(path)
    except ValueError as e:
        return f"Error: {e}"

    try:
        if file_path.exists():
            return update_file(file_path, old_str, new_str)
        else:
            return create_file(file_path, new_str)
    except Exception:
        return "Error: Couldn't write to file!"


def glob_files(pattern: str, path: str | None = None) -> str:
    """
    Searches for files and directories matching a glob pattern.
    If no path is provided, searches from the current directory.
    Supports recursive search using '**' (e.g., '**/*.py').
    """
    try:
        dir_path = get_safe_path(path)
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
