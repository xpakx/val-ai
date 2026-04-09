from pathlib import Path


def get_weather(city: str) -> str:
    """
    Fetches the current weather for a specific city.
    """
    if "london" in city.lower():
        return "15°C and cloudy"
    return "22°C and sunny"


def read_file(path: str):
    """
    Reads the file on filesystem in a folder agent runs in
    """
    file_path = Path(path)
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
    if path is None:
        path = ""
    dir_path = Path(path)
    if not dir_path.is_dir():
        return "Error: File is not a directory"

    files = [(f'{f.name}/' if f.is_dir() else f.name) for f in dir_path.iterdir()]
    return "\n".join(files)
