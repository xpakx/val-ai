from pathlib import Path
from configparser import ConfigParser
import sqlite3
import msgspec
from datetime import datetime, timedelta

from agent.config import get_xdg_data_location


PRIME_EPOCH = datetime(1970, 1, 1)


class BookmarkData(msgspec.Struct):
    title: str
    url: str
    added: str
    timestamp: int
    rev_domain: int


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


def find_firefox_db() -> Path:
    root_path = find_firefox_data()
    config = load_ini_file(root_path)
    profile = find_default_profile(config, root_path)
    db_path = profile / "places.sqlite"
    if not db_path.exists():
        raise FileNotFoundError(
                f"places.sqlite not found in the profile path: {profile}"
        )

    return db_path


def prtime_to_datetime(pr_time: int) -> str:
    if pr_time is None:
        return ""
    dt = PRIME_EPOCH + timedelta(microseconds=pr_time)
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def get_bookmarks(db_path: Path) -> list[BookmarkData]:
    print(f"Connecting to database: {db_path}")
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cursor = conn.cursor()
        # TODO: more options/strategies for extraction
        # MAYBE: clean after extraction
        SQL_QUERY = """
        SELECT
            p.title,
            p.url,
            b.dateAdded,
            p.rev_host
        FROM
            moz_bookmarks b
        JOIN
            moz_places p ON b.fk = p.id
        WHERE
            b.type = 1 AND p.url IS NOT NULL
            AND b.dateAdded > (strftime('%s', 'now') * 1000000 - 86400000000)
        ORDER BY
            b.dateAdded DESC;
        """

        bookmarks = []
        cursor.execute(SQL_QUERY)
        for title, url, date_added_prtime, rev_domain in cursor:
            if url.startswith("place:"):
                continue
            clean_title = title.strip() if title else url
            # TODO: better typing
            bookmarks.append(
                    BookmarkData(
                        title=clean_title,
                        url=url,
                        added=prtime_to_datetime(date_added_prtime),
                        timestamp=date_added_prtime,
                        rev_domain=rev_domain,
                    )
            )
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e):
            raise Exception("WARNING: The database is locked. Ensure Firefox is closed or try again.")

    finally:
        conn.close()

    print(f"Extracted {len(bookmarks)} bookmarks.")
    return bookmarks


def get_bookmarks_by_name(db_path: Path, name: str) -> list[BookmarkData]:
    print(f"Connecting to database: {db_path}")
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cursor = conn.cursor()

        SQL_QUERY = f"""
        SELECT
            p.title,
            p.url,
            b.dateAdded,
            p.rev_host
        FROM
            moz_bookmarks b
        JOIN
            moz_places p ON b.fk = p.id
        WHERE
            b.type = 1 AND p.url IS NOT NULL
            AND p.title LIKE '%{name}%'
        ORDER BY
            b.dateAdded DESC;
        """

        bookmarks = []
        cursor.execute(SQL_QUERY)
        for title, url, date_added_prtime, rev_domain in cursor:
            if url.startswith("place:"):
                continue
            clean_title = title.strip() if title else url
            bookmarks.append(
                    BookmarkData(
                        title=clean_title,
                        url=url,
                        added=prtime_to_datetime(date_added_prtime),
                        timestamp=date_added_prtime,
                        rev_domain=rev_domain,
                    )
            )
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e):
            raise Exception("WARNING: The database is locked. Ensure Firefox is closed or try again.")
    finally:
        conn.close()

    print(f"Extracted {len(bookmarks)} bookmarks.")
    return bookmarks


if __name__ == "__main__":
    db = find_firefox_db()
    print(get_bookmarks(db))
