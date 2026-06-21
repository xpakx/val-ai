import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathspec import PathSpec
from pathlib import Path

# TODO: patterns and file ignoring
# TODO: patterns and ignore_patterns should be constructed based
#       on defined events


class GitIgnoreHandler(FileSystemEventHandler):
    def __init__(self, root_path, spec: PathSpec,
                 ignore_directories: bool):
        self.root_path = Path(root_path).resolve()
        self.spec = spec
        self.ignore_directories = ignore_directories

    def dispatch(self, event):
        if self.ignore_directories and event.is_directory:
            return
        if self.is_ignored(event.src_path):
            return
        if event.event_type == 'moved' and self.is_ignored(event.dest_path):
            return

        super().dispatch(event)

    def is_ignored(self, path_str: str):
        try:
            abs_path = Path(path_str).resolve()
            rel_path = abs_path.relative_to(self.root_path)
            return self.spec.match_file(rel_path.as_posix())
        except ValueError:
            return True


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

        def on_created(event):
            self.on_created(event)

        def on_deleted(event):
            self.on_deleted(event)

        def on_moved(event):
            self.on_moved(event)

        self.handler.on_modified = on_modified
        self.handler.on_created = on_created
        self.handler.on_deleted = on_deleted
        self.handler.on_moved = on_moved
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
            lambda: self._dispatch("file_changed", event.src_path)
        )

    def on_created(self, event):
        self.loop.call_soon_threadsafe(
                self._dispatch, "file_created", event.src_path)

    def on_deleted(self, event):
        self.loop.call_soon_threadsafe(
                self._dispatch, "file_deleted", event.src_path)

    def on_moved(self, event):
        self.loop.call_soon_threadsafe(
                self._dispatch, "file_moved", event.src_path)

    def _dispatch(self, event_name: str, path: str):
        self._timers.pop(path, None)
        asyncio.create_task(self.app.emit(event_name, path))

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
