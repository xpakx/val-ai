import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class AsyncWatchdogHandler(FileSystemEventHandler):
    def __init__(self, app, loop):
        self.app = app
        self.loop = loop

    def on_modified(self, event):
        if not event.is_directory:
            print("EVENT", event.src_path)
            print(event)
            self.loop.call_soon_threadsafe(
                lambda: asyncio.create_task(self.app.emit("file_changed", event.src_path))
            )


class WatchdogFeature:
    def __init__(self, path: str = '.'):
        self.path = path

    async def run(self, app):
        loop = asyncio.get_running_loop()
        self.handler = AsyncWatchdogHandler(app, loop)
        self.observer = Observer()
        self.observer.schedule(self.handler, self.path, recursive=True)

        self.observer.start()
        try:
            while True:
                await asyncio.sleep(1)
        finally:
            self.observer.stop()
            self.observer.join()
