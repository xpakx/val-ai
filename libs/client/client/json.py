from typing import Literal, TypeVar, cast, get_args, get_origin

import msgspec

T = TypeVar("T")


class JsonRescuer:
    def _rescue_imperfect_json(self, text: str, target_type: type[T]) -> T:
        # TODO: we should probably found all potential
        # candidates and check whether they are proper
        # json
        new_text = self._find_json(text)
        if new_text:
            return msgspec.json.decode(new_text, type=target_type)

        origin = get_origin(target_type)
        inner_type = get_args(target_type)[0]
        if origin is list:
            new_text = self._find_json(text, start_symbol="{")
            if new_text:
                return cast(T, [msgspec.json.decode(new_text, type=inner_type)])
        if origin is list:
            return cast(T, [inner_type(text)])
        raise ValueError(f"Could not rescue JSON into requested type: {target_type}")

    def _is_valid_json(self, text: str) -> bool:
        try:
            msgspec.json.decode(text, type=msgspec.Raw)
            return True
        except msgspec.DecodeError:
            return False

    def _find_json(
        self, text: str, start_symbol: Literal["[", "{"] = "["
    ) -> str | None:
        print("rescuing json")
        end_symbol = "]" if start_symbol == "[" else "}"
        start_index = text.find(start_symbol)
        if start_index == -1:
            return None

        counter = 0
        for i in range(start_index, len(text)):
            if text[i] == start_symbol:
                counter += 1
            elif text[i] == end_symbol:
                counter -= 1
            if counter == 0:
                potential_text = text[start_index : i + 1]
                if self._is_valid_json(potential_text):
                    return potential_text
        return None
