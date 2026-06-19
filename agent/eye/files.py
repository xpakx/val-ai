import asyncio
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

# TODO: patterns and file ignoring
# TODO: use .gitignore with pathspec by default
# TODO: patterns and ignore_patterns should be constructed based
#       on defined events
# TODO: on_deleted/on_moved/on_created


class WatchdogFeature:
    def __init__(self, path: str = '.', debounce: float = 0.3):
        self.path = path
        self._timers = {}
        self.debounce = debounce

    async def run(self, app):
        self.loop = asyncio.get_running_loop()
        self.app = app

        self.handler = PatternMatchingEventHandler(
            # patterns=["*.py"],
            ignore_patterns=["4913"],  # neovim temporary file
            ignore_directories=True,
            case_sensitive=False
        )

        def on_modified(event):
            self.on_modified(event)

        self.handler.on_modified = on_modified
        self.observer = Observer()
        self.observer.schedule(self.handler, self.path, recursive=True)

        self.observer.start()
        try:
            while True:
                await asyncio.sleep(1)
        finally:
            self.observer.stop()
            self.observer.join()

    def on_modified(self, event):
        if event.src_path in self._timers:
            self._timers[event.src_path].cancel()
        self._timers[event.src_path] = self.loop.call_later(
            self.debounce,
            lambda: self._dispatch(event.src_path)
        )

    def _dispatch(self, path: str):
        self._timers.pop(path, None)
        asyncio.create_task(self.app.emit("file_changed", path))
