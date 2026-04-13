import time
from typing import Callable


def fibonacci_backoff(task: Callable, max_attempts: int, start_index: int = 0):
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
