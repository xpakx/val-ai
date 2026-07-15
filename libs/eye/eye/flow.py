import asyncio
from eye.eye import Eye, EyeService
from typing import Callable, Any, Self, cast
from inspect import iscoroutinefunction
from dataclasses import dataclass, field


@dataclass
class WaitFor:
    signal_name: str


FlowStep = Callable | str | WaitFor


@dataclass
class LoopContext:
    count: int
    pending_signals: dict[str, asyncio.Event] = field(default_factory=dict)
    data: dict[str, Any] = field(default_factory=dict)

    def next(self) -> Self:
        return LoopContext(count=self.count+1)


class FlowFeature(EyeService):
    def __init__(
            self, name: str,
            flow_definition: list[FlowStep | tuple[FlowStep, ...]],
            deployable: bool = False
            ):
        self.name = name
        self.flow_definition = flow_definition
        self.next_loop_id = 0
        self.loops: dict[int, LoopContext] = {}
        self.deployable = deployable
        self.app = None

    def resume_signal(self, loop_id: int, signal_name: str):
        loop = self.loops.get(loop_id)
        if not loop:
            return
        if signal_name in loop.pending_signals:
            loop.pending_signals[signal_name].set()

    @property
    def event(self) -> list[str]:
        events = [f"{self.name}:loop_done"]
        for step_group in self.flow_definition:
            if isinstance(step_group, tuple):
                for step in step_group:
                    if isinstance(step, str):
                        events.append(step)
            elif isinstance(step_group, str):
                events.append(step_group)
        return events

    def init(self, app: Eye) -> None:
        if self.deployable:
            app.add_event(f"{self.name}:start", self.on_deployment)
        self.app = app

    def get_loop(self) -> LoopContext:
        loop = LoopContext(self.next_loop_id)
        self.next_loop_id += 1
        self.loops[loop.count] = loop
        return loop

    def _listen(self, wait_for: WaitFor, loop: LoopContext):
        async def on_signal():
            self.resume_signal(loop.count, wait_for.signal_name)
        return app.add_event(wait_for.signal_name, on_signal)

    def _unlisten(self, event):
        app.remove_event(event)

    async def on_deployment(self, event):
        loop = self.get_loop()
        asyncio.create_task(self.run_once(app, loop))

    async def run(self, app: Eye) -> None:
        if self.deployable:
            return
        while True:
            loop = self.get_loop()
            await self.run_once(app, loop)

    async def run_once(self, app: Eye, ctx: LoopContext) -> None:
        for step_group in self.flow_definition:
            if isinstance(step_group, tuple):
                tasks = [self._execute_step(app, s, ctx) for s in step_group]
                await asyncio.gather(*tasks)
            else:
                await self._execute_step(app, step_group, ctx)

        await app.emit(f"{self.name}:loop_done", loop=ctx)

    async def _execute_step(
            self, app: Eye, step: FlowStep, ctx: LoopContext) -> None:
        if isinstance(step, WaitFor):
            app_event = self._listen(step, ctx)
            event = asyncio.Event()
            ctx.pending_signals[step.signal_name] = event
            await event.wait()
            ctx.pending_signals.pop(step.signal_name, None)
            self._unlisten(app_event)
        elif isinstance(step, str):
            await app.emit(step)
        elif iscoroutinefunction(step):
            await step(app)
        elif callable(step):
            step(app)
        else:
            raise ValueError(f"Invalid flow step: {step}")


if __name__ == "__main__":
    async def step1(app: Eye):
        print("step 1")

    async def step2(app: Eye):
        print("step 2")
        await asyncio.sleep(1.5)
        print("step 2 done")

    async def step3(app: Eye):
        print("step 3")
        await asyncio.sleep(0.5)
        print("step 3 done")

    def step4(app: Eye):
        print("step 4")

    flow = [
            step1,
            "interrupting_event",
            (step2, step3),
            step4,
            WaitFor('test')
    ]
    app = Eye()
    app.add_service(FlowFeature("test", cast(list[FlowStep | tuple[FlowStep, ...]], flow)))
    from .files import WatchdogFeature
    app.add_service(WatchdogFeature())

    @app.on('test:loop_done')
    async def on_loop_done(loop):
        print(f"test: starting loop {loop.count}")

    @app.on('interrupting_event')
    async def on_event():
        print("interruption")

    @app.on('file_changed')
    async def on_file(path):
        print(f"FILE: {path}")
        await app.emit('test')

    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        pass
