import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class AsyncWatchdogHandler(FileSystemEventHandler):
    def __init__(self, app, loop, debounce: float = 0.3):
        self.app = app
        self.loop = loop
        self.debounce = debounce
        self._timers = {}

    def on_modified(self, event):
        if event.is_directory:
            return
        # neovim temporary file
        if event.src_path.endswith('4913'):
            return
        if event.src_path in self._timers:
            self._timers[event.src_path].cancel()
        # print("EVENT", event.src_path)
        # print(event)
        self._timers[event.src_path] = self.loop.call_later(
            self.debounce,
            lambda: self._dispatch(event.src_path)
        )

    def _dispatch(self, path: str):
        self._timers.pop(path, None)
        asyncio.create_task(self.app.emit("file_changed", path))


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
