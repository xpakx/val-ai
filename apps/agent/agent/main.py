from client import Client
from client.fibonacci import fibonacci_delays
from client.config import load_config
from tools.toolgen import get_tool
from tools.tools import FileTool

from agent.chat import Chat
from agent.search.search import search
from agent.systemparts import current_time
from agent.systemprompt import get_system_prompt_info
from agent.ui import CLIProvider


def prepare_tools(chat: Chat) -> None:
    tools = FileTool()
    for tool in tools.tools():
        chat.add_tool(tool)
    chat.add_tool(get_tool(search))


def main(tools):
    config = load_config("data/config.json")
    client = Client(config, fibonacci_delays)
    chat = Chat(client, CLIProvider(), tool_support=tools)
    prepare_tools(chat)

    time = get_system_prompt_info(current_time)
    chat.add_system_part(time)
    print(chat.prompt.generate())

    chat.run()


def test():
    import msgspec
    from context import Context

    class Msg(msgspec.Struct):
        message: str

    config = load_config("data/config.json")
    client = Client(config, fibonacci_backoff)
    context = Context()
    context.push("user", "hello, how are you?")
    resp = client.call_api(
        context.get_messages(),
        response_format=Msg,
    )
    msg = resp.choices[0].message.content
    if not msg:
        return
    result = msgspec.json.decode(msg, type=Msg)
    print(result)


if __name__ == "__main__":
    main(True)
    # test()
