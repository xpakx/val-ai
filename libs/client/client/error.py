from typing import Protocol
from requests import Response
import msgspec
from client.typedefs import GoogleErrorWrapper


class ErrorProcessor(Protocol):
    def check_for_retry(self, http_response: Response) -> int | None: ...


class GoogleErrorProcessor(ErrorProcessor):
    def check_for_retry(self, http_response: Response) -> int | None:
        if http_response.status_code != 429:
            return
        err = msgspec.json.decode(
                http_response.text,
                type=list[GoogleErrorWrapper]
        )[0]
        print(err)
        details = err.error.details
        delay = None
        for d in details:
            if d.retryDelay:
                delay = d.retryDelay
                break
        if delay is None:
            return None
        print(delay)
        # TODO: other providers
        # TODO: google info about delay very often is wrong
        # TODO: sometimes time could prolly be longer than 59s
        delay = int(delay[:-1])
        return delay
