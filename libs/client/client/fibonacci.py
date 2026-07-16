import time
import asyncio
from typing import Callable, TypeVar, Awaitable

T = TypeVar("T")


def fibonacci_backoff(
        task: Callable[[], T],
        max_attempts: int,
        start_index: int = 0
) -> T | None:
    a, b = 1, 1
    i = 0
    for _ in range(start_index):
        a, b = b, a + b

    while i < max_attempts:
        try:
            result = task()
        except Exception as e:
            print(f"Task failed: {e}")
        else:
            print("Task finished successfully!")
            return result

        print(f"Retrying in {a}s...")
        time.sleep(a)
        a, b = b, a + b
        i += 1

    print("Max attempts reached, giving up.")
    return None


async def fibonacci_backoff_async(
    task: Callable[[], Awaitable[T]],
    max_attempts: int,
    start_index: int = 0
) -> T | None:
    a, b = 1, 1
    i = 0
    for _ in range(start_index):
        a, b = b, a + b

    while i < max_attempts:
        try:
            result = await task()
        except Exception as e:
            print(f"Task failed: {e}")
        else:
            print("Task finished successfully!")
            return result

        print(f"Retrying in {a}s...")
        await asyncio.sleep(a)
        a, b = b, a + b

    print("Max attempts reached, giving up.")
    return None
