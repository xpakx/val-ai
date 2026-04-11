from typing import Protocol, Any


class UIProvider(Protocol):
    def print(self, text: str) -> None: ...
    def debug(self, text: Any) -> None: ...
    def say(self, actor: str, text: str) -> None: ...
    def get_input(self) -> str: ...


DEBUG = False


class CLIProvider:
    def print(self, text: str) -> None:
        print(text)

    def debug(self, text: Any) -> None:
        if not DEBUG:
            return
        print(text)

    def say(self, actor: str, text: str) -> None:
        if actor == 'Agent':
            print(f"\033[94m{actor}\033[0m:", end=" ")
            print(text)
        else:
            print(f"\033[33m{actor}\033[0m:", end=" ")
            print(text)

    def get_input(self) -> str:
        return input("\033[33mUser\033[0m: ")
