import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathspec import PathSpec
from pathlib import Path

# TODO: patterns and file ignoring
# TODO: patterns and ignore_patterns should be constructed based
#       on defined events


class GitIgnoreHandler(FileSystemEventHandler):
    def __init__(self, router: "WatchdogFeature",
                 root_path, spec: PathSpec,
                 ignore_directories: bool):
        self.root_path = Path(root_path).resolve()
        self.spec = spec
        self.ignore_directories = ignore_directories
        self.router = router

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

    def on_modified(self, event):
        self.router.on_modified(event)

    def on_created(self, event):
        self.router.on_created(event)

    def on_deleted(self, event):
        self.router.on_deleted(event)

    def on_moved(self, event):
        self.router.on_moved(event)


class WatchdogEventRouter:
    def __init__(self, path, loop, app, debounce: float = 0.3):
        self.path = path
        self._timers = {}
        self.debounce = debounce
        self.loop = loop
        self.app = app
        self.handler = None
        self.watch = None 
        self.modified = "file_changed"

    def set_handler(self, handler):
        self.handler = handler

    def set_watch(self, watch):
        self.watch = watch

    def on_modified(self, event):
        self.loop.call_soon_threadsafe(
                self._handle_modified, event.src_path)

    def _handle_modified(self, path: str):
        if path in self._timers:
            self._timers[path].cancel()
        self._timers[path] = self.loop.call_later(
            self.debounce,
            lambda: self._dispatch_debounced(self.modified, path)
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
        self.loop.create_task(self.app.emit(event_name, path))

    def _dispatch_debounced(self, event_name: str, path: str):
        self._timers.pop(path, None)
        self._dispatch(event_name, path)


class WatchdogFeature:
    def __init__(self, path: str = '.', debounce: float = 0.3,
                 ignore_hidden: bool = True):
        self.path = path
        self.debounce = debounce
        self.ignore_hidden = ignore_hidden
        self.active_watches = {}
        self.observer = None
        self.name = 'watchdog'
        self.loop = None
        self.app = None

    async def run(self, app):
        self.loop = asyncio.get_running_loop()
        self.app = app
        self._stop_event = asyncio.Event()

        spec = self._prepare_ignore_patterns()

        self.main_event_router = WatchdogEventRouter(
                self.path,
                self.loop,
                self.app,
                self.debounce
        )
        handler = GitIgnoreHandler(
                router=self.main_event_router,
                spec=spec,
                ignore_directories=True,
                root_path=self.path
        )
        self.main_event_router.set_handler(handler)

        self.observer = Observer()
        self.observer.schedule(handler, self.path, recursive=True)
        self._do_add_routes()

        self.observer.start()
        try:
            await self._stop_event.wait()
        finally:
            self.observer.stop()
            self.observer.join()

    def _prepare_ignore_patterns(self) -> PathSpec:
        # neovim temporary file
        result = ["4913"]
        if self.ignore_hidden:
            result.append(".*")
        gitignore = self._use_gitignore(Path(self.path) / ".gitignore")
        if gitignore:
            result.extend(gitignore)
        print(result)
        spec = PathSpec.from_lines('gitwildmatch', result)
        return spec

    def _use_gitignore(self, path):
        if not path.exists():
            return None
        data = path.read_text().splitlines()
        return [line for line in data if line and not line.startswith('#')]

    def stop(self):
        self._stop_event.set()

    def _do_add_route(self, path: Path, event_name: str):
        class RoutedHandler(FileSystemEventHandler):
            def __init__(self, router, name):
                self.router = router

            def dispatch(self, event):
                if event.event_type != 'modified':
                    return
                self.router.on_modified(event)

        router = WatchdogEventRouter(
                path, self.loop, self.app, self.debounce)
        router.modified = event_name
        handler = RoutedHandler(router, event_name)
        router.set_handler(handler)

        if self.loop:
            self._start_router()
        self.active_watches[path] = router

    def _start_router(self, router: WatchdogEventRouter):
        watch = self.observer.schedule(
                router.handler,
                path=str(router.path),
                recursive=True
        )
        router.set_watch(watch)

    def add_route(self, path: str | Path, event_name: str):
        resolved_path = Path(path).resolve()
        self._do_add_route(resolved_path, event_name)

    def _do_add_routes(self):
        for path, router in self.active_watches.items():
            if router.loop is None:
                router.loop = self.loop
                router.app = self.app
                self._start_router(router)

    def remove_route(self, path: str | Path):
        resolved_path = Path(path).resolve()
        if resolved_path in self.active_watches:
            handler = self.active_watches[resolved_path]
            if handler.watch:
                self.observer.unschedule(handler.watch)
            del self.active_watches[resolved_path]
