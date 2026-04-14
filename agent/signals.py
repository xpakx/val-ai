class Observable:
    def __init__(self):
        self._observers = []

    def _subscribe(self, observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def _notify(self):
        for observer in self._observers:
            observer.update()


class Signal(Observable):
    def __init__(self, value):
        super().__init__()
        self._value = value

    def __call__(self):
        return self._value

    def set(self, new_value):
        if self._value != new_value:
            self._value = new_value
            self._notify()


class Computed(Observable):
    def __init__(self, fn, deps):
        super().__init__()
        self._fn = fn
        self._deps = deps
        self._value = None

        for dep in self._deps:
            dep._subscribe(self)

        self.update()

    def update(self):
        new_value = self._fn(*[d() for d in self._deps])
        if self._value != new_value:
            self._value = new_value
            self._notify()

    def __call__(self):
        return self._value


class Effect:
    def __init__(self, fn, deps):
        self._fn = fn
        self._deps = deps
        for dep in self._deps:
            dep._subscribe(self)
        self.update()

    def update(self):
        self._fn(*[d() for d in self._deps])


if __name__ == "__main__":
    count = Signal(10)
    multiplier = Signal(2)

    total = Computed(
        fn=lambda c, m: c * m,
        deps=[count, multiplier]
    )

    is_even = Computed(
        fn=lambda t: t % 2 == 0,
        deps=[total]
    )

    Effect(
        fn=lambda t, e: print(f"Total is {t}, Even: {e}"),
        deps=[total, is_even]
    )

    multiplier.set(3)
    count.set(7)
