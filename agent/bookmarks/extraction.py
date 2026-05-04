from typing import Protocol
from agent.bookmarks.loader import find_firefox_db, get_bookmarks
from agent.bookmarks.loader import BookmarkData


class ProcessAction(Protocol):
    def process(self, bookmark: BookmarkData) -> None: ...
    def compare(self, bookmark: BookmarkData) -> bool: ...


class BookmarkExtractor:
    def __init__(self):
        self.db = find_firefox_db()
        self.actions: list[ProcessAction] = []

    def process(self):
        bookmarks = get_bookmarks(self.db)
        for bookmark in bookmarks:
            self.process_bookmark(bookmark)

    def process_bookmark(self, bookmark: BookmarkData):
        for action in self.actions:
            if action.compare(bookmark):
                action.process(bookmark)

    def add_action(self, action: ProcessAction):
        self.actions.append(action)


class PrintAction:
    def __init__(self):
        self.domain = None

    def process(self, bookmark: BookmarkData) -> None:
        print(bookmark.title)
        print(bookmark.url)
        print(bookmark.rev_domain)

    def compare(self, bookmark: BookmarkData) -> bool:
        return True


if __name__ == "__main__":
    bookmarks = BookmarkExtractor()
    bookmarks.add_action(PrintAction())
    bookmarks.process()
