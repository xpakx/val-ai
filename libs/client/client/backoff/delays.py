from collections.abc import Iterable, Iterator
import random


def fibonacci_delays(start_index: int = 0) -> Iterator[float]:
    a, b = 1.0, 1.0
    for _ in range(start_index):
        a, b = b, a + b
    while True:
        yield a
        a, b = b, a + b


def exponential_delays(
    base: float = 1.0, factor: float = 2.0, max_delay: float | None = None
) -> Iterator[float]:
    delay = base
    while True:
        yield min(delay, max_delay) if max_delay is not None else delay
        delay *= factor


def constant_delays(interval: float = 1.0) -> Iterator[float]:
    while True:
        yield interval


def add_jitter(delays: Iterable[float], jitter_range: float = 0.2) -> Iterator[float]:
    for d in delays:
        low = d * (1.0 - jitter_range)
        high = d * (1.0 + jitter_range)
        yield max(0.0, random.uniform(low, high))
