from typing import Literal

import msgspec
from tools.toolgen import Parameters, Property

from client.typedefs import OpenAIResponseFormat, OpenAIResponseSchema


def format_type(tp: type) -> Literal["string", "integer", "number", "boolean", "null"]:
    # TODO
    if tp is str:
        return "string"
    if tp is int:
        return "integer"
    if tp is float:
        return "number"
    if tp is bool:
        return "boolean"
    return "null"


def prepare_response_format(tp: type[msgspec.Struct]) -> OpenAIResponseFormat:
    name = tp.__name__.lower()
    properties = {}
    for field in msgspec.structs.fields(tp):
        type_str = format_type(field.type)
        properties[field.name] = Property(type=type_str)
    schema = Parameters(
        required=list(properties.keys()),
        additional_properties=False,
        properties=properties,
    )
    json_schema = OpenAIResponseSchema(name=name, schema=schema)
    return OpenAIResponseFormat(json_schema=json_schema)
