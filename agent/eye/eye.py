import asyncio
import secrets
import inspect
from typing import Callable, Protocol, Any
from dataclasses import dataclass


class EyeService(Protocol):
    async def run(self, app: "Eye") -> None: ...

    @property
    def event(self) -> list[str]: return []
    def has_logic(self) -> bool: return False
    def get_injectable(self) -> Any | None | dict[str, Any]: return None


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
        self._injectables: dict[str, Any] = {}

    # TODO: smart registration of services
    def on(self, event_name: str) -> Callable:
        def decorator(func: Callable) -> Callable:
            self.add_event(event_name, func)
            return func
        return decorator

    def add_event(self, event_name: str, func: Callable) -> None:
        handler = self._prepare_event_handler(event_name, func)
        if event_name not in self._events:
            self._events[event_name] = []
        self._events[event_name].append(handler)

    def _prepare_event_handler(
            self, event_name: str, func: Callable) -> EventHandler:
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
        if service_func.has_logic():
            injectable = service_func.get_injectable()
            if isinstance(injectable, dict):
                collisions = self._injectables.keys() & injectable.keys()
                if collisions:
                    print(f"Warning: Overwriting keys: {collisions}")
                self._injectables.update(injectable)
            else:
                self._injectables[service_func.name] = injectable
        return name

    def get_service(self, name: str) -> EyeService | None:
        return self._services.get(name)

    async def emit(self, event_name: str, **kwargs) -> None:
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
    def prepare_event(
            self, handler: EventHandler, tasks: list, ctx: dict[str, Any]
    ) -> None:
        args = []
        for arg_name in handler.args:
            if arg_name in ctx:
                args.append(ctx[arg_name])
            elif arg_name in self._injectables:
                args.append(self._injectables.get(arg_name))
            elif arg_name == 'event':
                args.append(ctx)
            else:
                args.append(None)
        tasks.append(handler.func(*args))

    async def run(self) -> None:
        tasks = []
        for _, service in self._services.items():
            if hasattr(service, 'init'):
                service.init(self)
            if hasattr(service, 'run'):
                tasks.append(
                        asyncio.create_task(service.run(self)))
        print("App running. Press Ctrl+C to stop.")
        await asyncio.gather(*tasks)

    def _generate_random_id(self) -> str:
        n = secrets.randbits(64)
        chars = "0123456789abcdefghijklmnopqrstuvwxyz"
        result = ""
        while n > 0:
            n, rem = divmod(n, 36)
            result = chars[rem] + result
        return f"{result}"

    def add_injectable(self, name: str, injectable: Any) -> None:
        self._injectables[name] = injectable
