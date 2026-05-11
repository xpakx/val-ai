import msgspec
from agent.bookmarks.loader import find_firefox_db, get_bookmarks
from agent.bookmarks.loader import get_bookmarks_by_name


def bookmark_tool(name: str | None = None) -> str:
    """
    Loads users' bookmarks
    """
    db = find_firefox_db()
    if name:
        bookmarks = get_bookmarks_by_name(db, name)
    else:
        bookmarks = get_bookmarks(db)
    data = msgspec.json.encode(bookmarks)
    return data.decode('utf-8')
