from pathlib import Path
from agent.config import get_xdg_data_location


def find_firefox_data() -> Path:
    xdg_data_home = get_xdg_data_location()
    if xdg_data_home:
        root_path = Path(xdg_data_home) / "mozilla" / "firefox"
        if root_path.exists():
            return root_path

    return Path.home() / ".mozilla" / "firefox"


def load_ini_file(root_path: Path):
    profiles_ini = root_path / "profiles.ini"
    if not profiles_ini.exists():
        raise FileNotFoundError(
                f"profiles.ini not found in expected location: {profiles_ini}"
                )

    print(profiles_ini.read_text())


def find_firefox_profile() -> Path:
    root_path = find_firefox_data()
    load_ini_file(root_path)




if __name__ == "__main__":
    print(find_firefox_profile())
