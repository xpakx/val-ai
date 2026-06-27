from agent.eye.eye import Eye
from agent.eye.files import WatchdogFeature
from agent.eye.bookmarks import BookmarksFileFeature
import asyncio


app = Eye()


async def fake_sevice(app):
    while True:
        await app.emit("data_received", data={"id": 1, "value": 100})
        await asyncio.sleep(5)


@app.on("data_received")
async def handle_data(data):
    print(f"Event: Processed data {data}")


@app.on("file_changed")
async def on_file_change(path):
    print(f"Feature detected change: {path}")


@app.on("file_created")
async def on_file_creation(path):
    print(f"Feature detected creation: {path}")


@app.on("file_deleted")
async def on_file_deletion(path):
    print(f"Feature detected deletion: {path}")


@app.on("git_change")
async def on_git(path):
    print(f"Feature detected git change: {path}")


@app.on("bookmark_added")
async def on_bookmark(bookmark):
    print(f" - {bookmark['title'] or 'No Title'}: {bookmark['url']}")

# app.add_service(fake_sevice)
app.add_service(WatchdogFeature())
app.add_service(BookmarksFileFeature())

if __name__ == "__main__":
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        pass
