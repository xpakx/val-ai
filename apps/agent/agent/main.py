from client.config import load_config
from client.backoff import fibonacci_backoff
from client import Client
from tools.tools import FileTool
from tools.toolgen import get_tool
from agent.ui import CLIProvider
from agent.systemparts import current_time
from agent.systemprompt import get_system_prompt_info
from agent.chat import Chat
from agent.search.search import search


def prepare_tools(chat: Chat) -> None:
    tools = FileTool()
    for tool in tools.tools():
        chat.add_tool(tool)
    chat.add_tool(get_tool(search))


def main(tools):
    config = load_config("data/config.json")
    client = Client(config, fibonacci_backoff)
    chat = Chat(client, CLIProvider(), tool_support=tools)
    prepare_tools(chat)

    time = get_system_prompt_info(current_time)
    chat.add_system_part(time)
    print(chat.prompt.generate())

    chat.run()


def test():
    from context import Context
    import msgspec

    class Msg(msgspec.Struct):
        message: str
    config = load_config("data/config.json")
    client = Client(config, fibonacci_backoff)
    context = Context()
    context.push('user', 'hello, how are you?')
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
