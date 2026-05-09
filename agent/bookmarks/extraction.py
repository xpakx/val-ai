from typing import Protocol
from agent.bookmarks.loader import find_firefox_db, get_bookmarks
from agent.bookmarks.loader import BookmarkData


class ProcessAction(Protocol):
    def process(self, bookmark: BookmarkData) -> None: ...
    def compare(self, bookmark: BookmarkData) -> bool: ...
    def then(self, other: "ProcessAction") -> "ProcessAction": ...


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

    def add_action(self, action: ProcessAction) -> ProcessAction:
        self.actions.append(action)
        return action


class PrintAction:
    def __init__(self):
        self.next: ProcessAction | None = None

    def process(self, bookmark: BookmarkData) -> None:
        print(bookmark.title)
        print(bookmark.url)
        print(bookmark.rev_domain)

        if self.next:
            self.next.process(bookmark)

    def compare(self, bookmark: BookmarkData) -> bool:
        return True

    def then(self, other: ProcessAction) -> ProcessAction:
        self.next = other
        return other


class FilterAction:
    def __init__(self, domain: str):
        self.next: ProcessAction | None = None
        self.domain = domain

    def process(self, bookmark: BookmarkData) -> None:
        if self.next:
            self.next.process(bookmark)

    def compare(self, bookmark: BookmarkData) -> bool:
        return bookmark.url.find(self.domain) > 0

    def then(self, other: ProcessAction) -> ProcessAction:
        self.next = other
        return other


if __name__ == "__main__":
    bookmarks = BookmarkExtractor()
    (
            bookmarks
            .add_action(FilterAction("youtube.com"))
            .then(PrintAction())
    )
    bookmarks.process()
