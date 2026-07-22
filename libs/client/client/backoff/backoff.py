import asyncio
import time
from collections.abc import Awaitable, Callable, Iterable
from itertools import islice
from typing import TypeVar

T = TypeVar("T")


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
        islice(delays, max_attempts - 1) if max_attempts is not None else delays
    )
    for attempt, delay in enumerate(retry_delays, start=1):
        try:
            result = task()
            print("Task finished successfully!")
            return result
        except Exception as e:
            print(f"Attempt {attempt} failed ({e}). Retrying in {delay:.2f}s...")
            time.sleep(delay)
    try:
        result = task()
        print("Task finished successfully!")
        return result
    except Exception as e:
        print(f"Attempt {max_attempts} failed ({e}).")
        print("Max attempts reached, giving up.")
        return None


if __name__ == "__main__":
    from .delays import add_jitter, exponential_delays, fibonacci_delays

    def api_call() -> str:
        raise ValueError("Connection timed out")

    result = backoff_retry(
        task=api_call,
        delays=add_jitter(exponential_delays(base=0.5, factor=2.0, max_delay=30.0)),
        max_attempts=5,
    )

    result = backoff_retry(
        task=api_call,
        delays=fibonacci_delays(start_index=2),
        max_attempts=4,
    )

    result = backoff_retry(
        task=api_call,
        delays=exponential_delays(base=0.5, factor=2.0, max_delay=30.0),
        max_attempts=5,
    )

    result = backoff_retry(
        task=api_call,
        delays=[1.0, 2.0, 5.0, 10.0],
    )
