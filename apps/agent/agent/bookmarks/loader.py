import sqlite3
from configparser import ConfigParser
from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path
from typing import Protocol

import msgspec
from client.config import get_xdg_data_location

PRIME_EPOCH = datetime(1970, 1, 1)


class BookmarkData(msgspec.Struct):
    title: str
    url: str
    added: str
    timestamp: int
    rev_domain: str


class DbBridge(Protocol):
    def fetch_bookmarks(self) -> list[BookmarkData]: ...


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


def find_default_profile(config: ConfigParser, root_path: Path) -> Path | None:
    default_profile_path = None
    for section in config.sections():
        if section.startswith("Profile"):
            section_name = config.get(section, "Name", fallback="0")
            if section_name != "default-release":
                continue
            path_name = config.get(section, "Path")
            is_relative = config.getboolean(section, "IsRelative", fallback=True)

            if is_relative:
                default_profile_path = root_path / path_name
            else:
                default_profile_path = Path(path_name)
            return default_profile_path


def find_firefox_db() -> Path:
    root_path = find_firefox_data()
    config = load_ini_file(root_path)
    profile = find_default_profile(config, root_path)
    if not profile:
        raise FileNotFoundError("Couldn't find firefox profile")
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


def last_24h_query() -> str:
    return prepare_query(
        "b.dateAdded > (strftime('%s', 'now') * 1000000 - 86400000000)"
    )


def in_name_query(name: str) -> str:
    return prepare_query(f"p.title LIKE '%{name}%'")


def prepare_query(condition: str) -> str:
    return f"""
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
            AND {condition}
        ORDER BY
            b.dateAdded DESC;
        """


def fetch_bookmarks_from_db(db_path: Path, query: str) -> list[BookmarkData]:
    try:
        print(f"Connecting to database: {db_path}")
        with closing(
            sqlite3.connect(f"file:{db_path}?mode=ro&immutable=1", uri=True)
        ) as conn:
            cursor = conn.cursor()

            bookmarks = []
            cursor.execute(query)
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
            return bookmarks
    except sqlite3.OperationalError as e:
        if "database is locked" in str(e):
            raise Exception(
                "WARNING: The database is locked. Ensure Firefox is closed or try again."
            ) from e
        raise e


def get_bookmarks(db_path: Path) -> list[BookmarkData]:
    query = last_24h_query()
    bookmarks = fetch_bookmarks_from_db(db_path, query)
    print(f"Extracted {len(bookmarks)} bookmarks.")
    return bookmarks


def get_bookmarks_by_name(db_path: Path, name: str) -> list[BookmarkData]:
    query = in_name_query(name)
    bookmarks = fetch_bookmarks_from_db(db_path, query)
    print(f"Extracted {len(bookmarks)} bookmarks.")
    return bookmarks


class FirefoxBookmarkBridge:
    def __init__(self):
        self.db_path = find_firefox_db()

    def fetch_bookmarks(self) -> list[BookmarkData]:
        try:
            return get_bookmarks(self.db_path)
        except Exception as e:
            raise e


if __name__ == "__main__":
    db = find_firefox_db()
    print(get_bookmarks(db))
