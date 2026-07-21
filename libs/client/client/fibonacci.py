import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import TypeVar, Iterable, Iterator
from itertools import islice

T = TypeVar("T")


def fibonacci_backoff(
    task: Callable[[], T], max_attempts: int, start_index: int = 0
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
    task: Callable[[], Awaitable[T]], max_attempts: int, start_index: int = 0
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


def backoff_retry(
    task: Callable[[], T],
    delays: Iterable[float],
    max_attempts: int | None = None,
) -> T | None:
    retry_delays = (
        islice(delays, max_attempts - 1)
        if max_attempts is not None
        else delays
    )
    for attempt, delay in enumerate(retry_delays, start=1):
        try:
            result = task()
            print("Task finished successfully!")
            return result
        except Exception as e:
            print(
                f"Attempt {attempt} failed ({e}). Retrying in {delay:.2f}s..."
            )
            time.sleep(delay)
    try:
        result = task()
        print("Task finished successfully!")
        return result
    except Exception as e:
        print(f"Attempt {max_attempts} failed ({e}).")
        print("Max attempts reached, giving up.")
        return None


def fibonacci_delays(start_index: int = 0) -> Iterator[float]:
    a, b = 1.0, 1.0
    for _ in range(start_index):
        a, b = b, a + b
    while True:
        yield a
        a, b = b, a + b


if __name__ == "__main__":
    def api_call() -> str:
        raise ValueError("Connection timed out")

    result = backoff_retry(
        task=api_call,
        delays=fibonacci_delays(start_index=2),
        max_attempts=4,
    )
