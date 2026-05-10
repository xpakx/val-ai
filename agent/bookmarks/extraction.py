from typing import Protocol, Self
from agent.bookmarks.loader import FirefoxBookmarkBridge
from agent.bookmarks.loader import BookmarkData, DbBridge
import msgspec


class ProcessAction(Protocol):
    def process(self, bookmark: BookmarkData) -> None: ...
    def then(self, other: Self) -> Self: ...


class BookmarkExtractor:
    def __init__(self, db: DbBridge):
        self.bridge: DbBridge = db
        self.actions: list[ProcessAction] = []

    def process(self):
        bookmarks = self.bridge.fetch_bookmarks()
        for bookmark in bookmarks:
            self.process_bookmark(bookmark)

    def process_bookmark(self, bookmark: BookmarkData):
        for action in self.actions:
            action.process(bookmark)

    def add_action(self, action: ProcessAction) -> ProcessAction:
        self.actions.append(action)
        return action


class BaseAction:
    def __init__(self):
        self.next: ProcessAction | None = None

    def process(self, bookmark: BookmarkData) -> None:
        if self.next:
            self.next.process(bookmark)

    def then(self, other: ProcessAction) -> ProcessAction:
        self.next = other
        return other


class PrintAction(BaseAction):
    def process(self, bookmark: BookmarkData) -> None:
        print(bookmark.title)
        print(bookmark.url)
        print(bookmark.rev_domain)
        super().process(bookmark)


class FilterAction(BaseAction):
    def __init__(self, domain: str):
        self.domain = domain
        self.rev_domain = domain[::-1] + '.'
        super().__init__()

    def process(self, bookmark) -> None:
        if self.next and self.compare(bookmark):
            self.next.process(bookmark)

    def compare(self, bookmark: BookmarkData) -> bool:
        b_rev = bookmark.rev_domain
        return b_rev.startswith(self.rev_domain)


class RemoveSuffixAction(BaseAction):
    def __init__(self, suffix: str):
        self.suffix = suffix
        super().__init__()

    def process(self, bookmark: BookmarkData) -> None:
        title = bookmark.title.removesuffix(self.suffix).strip()
        b = msgspec.structs.replace(bookmark, title=title)
        super().process(b)


class RemovePrefixAction(BaseAction):
    def __init__(self, prefix: str):
        self.prefix = prefix
        super().__init__()

    def process(self, bookmark: BookmarkData) -> None:
        title = bookmark.title.removeprefix(self.prefix).strip()
        b = msgspec.structs.replace(bookmark, title=title)
        super().process(b)


if __name__ == "__main__":
    bookmarks = BookmarkExtractor(FirefoxBookmarkBridge())
    (
            bookmarks
            .add_action(FilterAction("youtube.com"))
            .then(RemoveSuffixAction("- Youtube"))
            .then(PrintAction())
    )
    bookmarks.process()
