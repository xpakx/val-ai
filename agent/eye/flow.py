import asyncio
from agent.eye.eye import Eye, EyeService
from typing import Callable
from inspect import iscoroutinefunction


class FlowFeature(EyeService):
    def __init__(
            self, name: str,
            flow_definition: list[Callable | tuple[Callable, ...]],
            ):
        self.name = name
        self.flow_definition = flow_definition

    async def run(self, app: Eye) -> None:
        loop_count = 1
        while True:
            for step_group in self.flow_definition:
                if isinstance(step_group, tuple):
                    tasks = [self._execute_step(app, s) for s in step_group]
                    await asyncio.gather(*tasks)
                else:
                    await self._execute_step(app, step_group)

            await app.emit(f"{self.name}:loop_done", loop=loop_count)
            loop_count += 1
            await asyncio.sleep(2.0)

    async def _execute_step(self, app: Eye, step: Callable) -> None:
        if iscoroutinefunction(step):
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

    flow = [step1, (step2, step3), step4]
    app = Eye()
    app.add_service(FlowFeature("test", flow))

    @app.on('test:loop_done')
    async def on_loop_done(loop: int):
        print(f"test: starting loop {loop}")
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        pass
