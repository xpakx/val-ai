import asyncio
from pathlib import Path
from agent.bookmarks.loader import find_firefox_db
import sqlite3
from eye.eye import EyeService


class BookmarksFileFeature(EyeService):
    def __init__(self, path: str = '.', debounce: float = 0.3,
                 ignore_hidden: bool = True):
        self.path = path
        self._timers = {}
        self.debounce = debounce
        self.ignore_hidden = ignore_hidden
        self.active_watches = {}
        self.watches_to_add = {}
        self.observer = None
        self.name = 'bookmarks_file'
        self.last_bookmark_timestamp = 0

    @property
    def event(self) -> list[str]:
        return ["bookmark_added"]

    def init(self, app):
        self.app = app
        watchdog_feature = app.get_service("watchdog")
        if not watchdog_feature:
            raise Exception('Boomark feature depends on watchdog feature!')
        self.db_path = find_firefox_db()
        event_name = '_internal_bookmark_db_modified'
        watchdog_feature.add_route(self.db_path, event_name)
        print(self.db_path)

        app.add_event(event_name, self.on_db_modified)

    async def on_db_modified(self, event):
        new_bookmarks = await asyncio.to_thread(self._fetch_new_bookmarks_sync)

        if not new_bookmarks:
            return
        self.last_bookmark_timestamp = new_bookmarks[-1]["date_added"]
        for bm in new_bookmarks:
            await self.app.emit('bookmark_added', bookmark=bm)

    async def run(self, app):
        pass

    def _fetch_new_bookmarks_sync(self) -> list:
        db_uri = Path(self.db_path).as_uri() + "?mode=ro&immutable=1"
        query = """
            SELECT b.id, b.title, p.url, b.dateAdded
            FROM moz_bookmarks b
            JOIN moz_places p ON b.fk = p.id
            WHERE b.type = 1 AND p.url IS NOT NULL AND b.dateAdded > ?

            AND b.dateAdded > (strftime('%s', 'now') * 1000000 - 86400000000)
            ORDER BY b.dateAdded ASC
        """

        new_bookmarks = []
        try:
            with sqlite3.connect(db_uri, uri=True) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, (self.last_bookmark_timestamp,))

                for row in cursor.fetchall():
                    new_bookmarks.append({
                        "id": row["id"],
                        "title": row["title"],
                        "url": row["url"],
                        "date_added": row["dateAdded"]
                    })
        except sqlite3.Error as e:
            print(f"SQLite reading error: {e}")

        return new_bookmarks
