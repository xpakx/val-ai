import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathspec import PathSpec
from pathlib import Path

# TODO: patterns and file ignoring
# TODO: patterns and ignore_patterns should be constructed based
#       on defined events
# TODO: on_deleted/on_moved/on_created


class GitIgnoreHandler(FileSystemEventHandler):
    def __init__(self, root_path, spec: PathSpec,
                 ignore_directories: bool):
        self.root_path = Path(root_path).resolve()
        self.spec = spec
        self.ignore_directories = ignore_directories

    def dispatch(self, event):
        if self.ignore_directories and event.is_directory:
            return
        abs_path = Path(event.src_path).resolve()

        try:
            rel_path = abs_path.relative_to(self.root_path)
            if self.spec.match_file(str(rel_path)):
                return
            super().dispatch(event)
        except ValueError:
            pass


class WatchdogFeature:
    def __init__(self, path: str = '.', debounce: float = 0.3,
                 ignore_hidden: bool = True):
        self.path = path
        self._timers = {}
        self.debounce = debounce
        self.ignore_hidden = ignore_hidden

    async def run(self, app):
        self.loop = asyncio.get_running_loop()
        self.app = app

        spec = self._prepare_ignore_patterns()

        self.handler = GitIgnoreHandler(
                spec=spec,
                ignore_directories=True,
                root_path=self.path
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

    def _prepare_ignore_patterns(self) -> PathSpec:
        # neovim temporary file
        result = ["4913"]
        if self.ignore_hidden:
            result.append(".*")
        gitignore = self._use_gitignore(Path("./.gitignore"))
        if gitignore:
            result.extend(gitignore)
        print(result)
        spec = PathSpec.from_lines('gitwildmatch', result)
        return spec

    def _use_gitignore(self, path):
        if not path.exists():
            return None
        return path.read_text().splitlines()
