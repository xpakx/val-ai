import asyncio
from agent.eye.eye import Eye, EyeService
from typing import Callable
from inspect import iscoroutinefunction


class FlowFeature(EyeService):
    def __init__(
            self, name: str,
            flow_definition: list[Callable],
            ):
        self.name = name
        self.flow_definition = flow_definition

    async def run(self, app: Eye) -> None:
        loop_count = 1
        while True:
            for step_group in self.flow_definition:
                await self._execute_step(app, step_group)

            await app.emit(f"{self.name}:loop_done", loop=loop_count)
            loop_count += 1
            await asyncio.sleep(0.5)

    async def _execute_step(self, app: "Eye", step: Callable) -> None:
        if iscoroutinefunction(step):
            await step(app)
        elif callable(step):
            step(app)
        else:
            raise ValueError(f"Invalid flow step: {step}")


if __name__ == "__main__":
    def step1(app: Eye):
        print("step 1")

    def step2(app: Eye):
        print("step 2")

    flow = [step1, step2]
    app = Eye()
    app.add_service(FlowFeature("test", flow))

    @app.on('test:loop_done')
    async def on_loop_done(loop: int):
        print(f"test: starting loop {loop}")
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        pass
