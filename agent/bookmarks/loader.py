from pathlib import Path
from configparser import ConfigParser

from agent.config import get_xdg_data_location


def find_firefox_data() -> Path:
    xdg_data_home = get_xdg_data_location()
    if xdg_data_home:
        root_path = Path(xdg_data_home) / "mozilla" / "firefox"
        if root_path.exists():
            return root_path

    return Path.home() / ".mozilla" / "firefox"


def load_ini_file(root_path: Path) -> ConfigParser:
    profiles_ini = root_path / "profiles.ini"
    if not profiles_ini.exists():
        raise FileNotFoundError(
                f"profiles.ini not found in expected location: {profiles_ini}"
        )

    config = ConfigParser()
    config.read(profiles_ini)
    return config


def find_default_profile(config: ConfigParser, root_path: Path) -> str | None:
    default_profile_path = None
    for section in config.sections():
        if section.startswith("Profile"):
            section_name = config.get(section, 'Name', fallback='0')
            if section_name != 'default-release':
                continue
            path_name = config.get(section, 'Path')
            is_relative = config.getboolean(
                    section, 'IsRelative', fallback=True)

            if is_relative:
                default_profile_path = root_path / path_name
            else:
                default_profile_path = Path(path_name)
            return default_profile_path


def find_firefox_profile() -> Path:
    root_path = find_firefox_data()
    config = load_ini_file(root_path)
    profile = find_default_profile(config, root_path)
    print(profile)


if __name__ == "__main__":
    find_firefox_profile()
