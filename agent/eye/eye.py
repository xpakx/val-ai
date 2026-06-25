import asyncio
import secrets
from typing import Callable, Protocol
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


class Eye:
    def __init__(self):
        self._events: dict[str, list[Callable]] = {}
        # TODO: fix type
        self._services: dict[str, EyeService] = {}

    # TODO: smart registration of services
    # TODO: smart params
    def on(self, event_name: str):
        def decorator(func: Callable):
            self.add_event(event_name, func)
            return func
        return decorator

    def add_event(self, event_name: str, func: Callable):
        if event_name not in self._events:
            self._events[event_name] = []
        self._events[event_name].append(func)

    def add_service(self, service_func: Callable | EyeService,
                    name: str | None = None):
        if not name and hasattr(service_func, "name"):
            name = service_func.name
        if not name:
            name = self._generate_random_id()
            # TODO: collisions
        if not hasattr(service_func, 'run'):
            service_func = SimpleEyeService(service_func, name)
            print(service_func)
        self._services[name] = service_func

    def get_service(self, name: str):
        return self._services.get(name)

    async def emit(self, event_name: str, *args, **kwargs):
        if event_name in self._events:
            tasks = [handler(*args, **kwargs) for handler in self._events[event_name]]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, Exception):
                    print(f"Error in handler for {event_name}: {res}")

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
        await app.emit("data_received", {"id": 1, "value": 100})
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
