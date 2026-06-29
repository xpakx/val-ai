import asyncio
from agent.eye.eye import Eye, EyeService
from typing import Callable, Any, Self
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
            ):
        self.name = name
        self.flow_definition = flow_definition
        self.loop = LoopContext(0)

    # TODO: currently this needs to be called manually,
    # but we want to just auto-register event listener later on
    def resume_signal(self, signal_name: str):
        if signal_name in self.loop.pending_signals:
            self.loop.pending_signals[signal_name].set()

    async def run(self, app: Eye) -> None:
        while True:
            # TODO: in the future we might want to dispatch
            # multiple runs in parallel every time we
            # receive some signal
            await self.run_once(app, self.loop)
            self.loop = self.loop.next()

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
            event = asyncio.Event()
            ctx.pending_signals[step.signal_name] = event
            await event.wait()
            ctx.pending_signals.pop(step.signal_name, None)
        elif isinstance(step, str):
            await app.emit(step)
        elif iscoroutinefunction(step):
            await step(app)
        elif callable(step):
            step(app)
        else:
            raise ValueError(f"Invalid flow step: {step}")


if __name__ == "__main__":
    def step1(app: Eye):
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

    flow = [step1, "interrupting_event", (step2, step3), step4, WaitFor('test')]
    app = Eye()
    app.add_service(FlowFeature("test", flow))
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
        service = app.get_service('test')
        if service:
            service.resume_signal('test')
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        pass
