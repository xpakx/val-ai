import asyncio
import secrets
import inspect
from typing import Callable, Protocol
from dataclasses import dataclass

from agent.eye.files import WatchdogFeature
from agent.eye.bookmarks import BookmarksFileFeature


class EyeService(Protocol):
    def run(self, app: "Eye") -> None: ...

    @property
    def event(self) -> list[str]: return []


class SimpleEyeService(EyeService):
    def __init__(self, func: Callable, name: str):
        self.name = name
        self.func = func

    def run(self, app: "Eye") -> None:
        return self.func(app)


@dataclass
class EventHandler():
    func: Callable
    args: list[str]


class Eye:
    def __init__(self):
        self._events: dict[str, list[EventHandler]] = {}
        self._services: dict[str, EyeService] = {}

    # TODO: smart registration of services
    def on(self, event_name: str):
        def decorator(func: Callable):
            self.add_event(event_name, func)
            return func
        return decorator

    def add_event(self, event_name: str, func: Callable):
        handler = self._prepare_event_handler(event_name, func)
        if event_name not in self._events:
            self._events[event_name] = []
        self._events[event_name].append(handler)

    def _prepare_event_handler(self, event_name: str, func: Callable):
        sig = inspect.signature(func)
        args = list(sig.parameters.keys())
        return EventHandler(func, args)

    def add_service(self, service_func: Callable | EyeService,
                    name: str | None = None) -> str:
        if not name and hasattr(service_func, "name"):
            name = service_func.name
        if not name:
            name = self._generate_random_id()
            # TODO: collisions
        if not hasattr(service_func, 'run'):
            service_func = SimpleEyeService(service_func, name)
            print(service_func)
        self._services[name] = service_func
        return name

    def get_service(self, name: str):
        return self._services.get(name)

    async def emit(self, event_name: str, **kwargs):
        if event_name not in self._events:
            return
        tasks = []
        for handler in self._events[event_name]:
            self.prepare_event(handler, tasks, kwargs)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for res in results:
            if isinstance(res, Exception):
                print(f"Error in handler for {event_name}: {res}")

    # TODO: perhaps a class for event context
    # TODO: services to inject
    def prepare_event(
            self, handler: EventHandler, tasks: list, ctx):
        args = []
        for arg_name in handler.args:
            if arg_name in ctx:
                args.append(ctx[arg_name])
            else:
                args.append(None)
        tasks.append(handler.func(*args))

    async def run(self):
        tasks = []
        for _, service in self._services.items():
            if hasattr(service, 'init'):
                service.init(self)
            if hasattr(service, 'run'):
                tasks.append(
                        asyncio.create_task(service.run(self)))
        print("App running. Press Ctrl+C to stop.")
        await asyncio.gather(*tasks)

    def _generate_random_id(self):
        n = secrets.randbits(64)
        chars = "0123456789abcdefghijklmnopqrstuvwxyz"
        result = ""
        while n > 0:
            n, rem = divmod(n, 36)
            result = chars[rem] + result
        return f"{result}"


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
async def on_bookmark(bm):
    print(f" - {bm['title'] or 'No Title'}: {bm['url']}")

# app.add_service(fake_sevice)
app.add_service(WatchdogFeature())
app.add_service(BookmarksFileFeature())

if __name__ == "__main__":
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        pass
