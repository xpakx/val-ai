import msgspec
from agent.client.typedefs import (
        OpenAIResponseFormat, OpenAIResponseSchema
)
from agent.toolgen import Parameters, Property


def format_type(tp: type) -> str:
    return 'string'  # TODO


def prepare_response_format(tp: msgspec.Struct) -> OpenAIResponseFormat:
    name = tp.__name__.lower()
    properties = {}
    for field in msgspec.structs.fields(tp):
        type_str = format_type(field.type)
        properties[field.name] = Property(
                type=type_str
        )
    schema = Parameters(
            required=list(properties.keys()),
            additionalProperties=False,
            properties=properties,
    )
    json_schema = OpenAIResponseSchema(
            name=name,
            schema=schema
    )
    return OpenAIResponseFormat(json_schema=json_schema)
