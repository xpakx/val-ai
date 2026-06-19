import asyncio
from typing import Callable, Dict, List
from agent.eye.files import WatchdogFeature


class Eye:
    def __init__(self):
        self._events: Dict[str, List[Callable]] = {}
        self._services: List[Callable] = []

    # TODO: smart registration of services
    # TODO: smart params
    def on(self, event_name: str):
        def decorator(func: Callable):
            if event_name not in self._events:
                self._events[event_name] = []
            self._events[event_name].append(func)
            return func
        return decorator

    def add_service(self, service_func: Callable):
        self._services.append(service_func)

    async def emit(self, event_name: str, *args, **kwargs):
        if event_name in self._events:
            tasks = [handler(*args, **kwargs) for handler in self._events[event_name]]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, Exception):
                    print(f"Error in handler for {event_name}: {res}")


    async def run(self):
        tasks = []
        for service in self._services:
            if hasattr(service, 'init'):
                service.init(self)
            if hasattr(service, 'run'):
                tasks.append(
                        asyncio.create_task(service.run(self)))
            else:
                tasks.append(asyncio.create_task(service(self)))
        print("App running. Press Ctrl+C to stop.")
        await asyncio.gather(*tasks)


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

app.add_service(fake_sevice)
app.add_service(WatchdogFeature())

if __name__ == "__main__":
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        pass
