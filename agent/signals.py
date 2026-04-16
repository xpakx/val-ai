from typing import Generic, TypeVar, Callable, Self

T = TypeVar("T")


class Observable(Generic[T]):
    def __init__(self):
        self._observers = []

    def _subscribe(self, observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def _notify(self):
        for observer in self._observers:
            observer.update()


class Signal(Observable[T]):
    def __init__(self, value: T):
        super().__init__()
        self._value = value

    def __call__(self) -> T:
        return self._value

    def set(self, new_value: T):
        if self._value != new_value:
            self._value = new_value
            self._notify()


class Computed(Observable[T]):
    def __init__(self, fn: Callable[..., T], deps: list[Signal | Self]):
        super().__init__()
        self._fn = fn
        self._deps = deps
        self._value = None

        for dep in self._deps:
            dep._subscribe(self)

        self.update()

    def update(self) -> None:
        new_value = self._fn(*[d() for d in self._deps])
        if self._value != new_value:
            self._value = new_value
            self._notify()

    def __call__(self) -> T | None:
        return self._value


class Effect:
    def __init__(self, fn: Callable, deps: list[Signal | Computed]):
        self._fn = fn
        self._deps = deps
        for dep in self._deps:
            dep._subscribe(self)
        self.update()

    def update(self) -> None:
        self._fn(*[d() for d in self._deps])


def signal(val: T) -> Signal[T]:
    return Signal(val)


def computed(
        fn: Callable[..., T],
        deps: list[Signal | Computed]
) -> Computed[T]:
    return Computed(fn, deps)


def effect(
        fn: Callable,
        deps: list[Signal | Computed]
) -> Effect:
    return Effect(fn, deps)


if __name__ == "__main__":
    count = signal(10)
    multiplier = signal(2)

    total = computed(
        fn=lambda c, m: c * m,
        deps=[count, multiplier]
    )

    is_even = computed(
        fn=lambda t: t % 2 == 0,
        deps=[total]
    )

    effect(
        fn=lambda t, e: print(f"Total is {t}, Even: {e}"),
        deps=[total, is_even]
    )

    multiplier.set(3)
    count.set(7)

    print(count())
