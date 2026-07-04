from agent.config import load_config
from agent.client import Client
from agent.toolgen import get_tool
from agent.ui import CLIProvider
from agent.tools import read_file, list_files, write_file, glob_files
from agent.systemparts import current_time
from agent.systemprompt import get_system_prompt_info
from agent.client.backoff import fibonacci_backoff
from agent.client.fibonacci import fibonacci_backoff_async
from agent.chat import Chat


def prepare_tools(chat: Chat) -> None:
    read_tool = get_tool(read_file)
    chat.add_tool(read_tool)
    list_tool = get_tool(list_files)
    chat.add_tool(list_tool)
    write_tool = get_tool(write_file)
    chat.add_tool(write_tool)
    glob_tool = get_tool(glob_files)
    chat.add_tool(glob_tool)


def main():
    config = load_config("data/config.json")
    client = Client(config, fibonacci_backoff)
    chat = Chat(client, CLIProvider())
    prepare_tools(chat)

    time = get_system_prompt_info(current_time)
    chat.add_system_part(time)

    chat.run()


def test():
    from agent.context import Context
    config = load_config("data/config.json")
    client = Client(config, fibonacci_backoff_async)
    chat = Chat(client, CLIProvider())
    prepare_tools(chat)
    conv = Context()
    conv.push('user', 'could you tell me what is in the Makefile?')
    read_tool = get_tool(read_file)
    resp = client.ask_with_tools(
            conv.get_messages(),
            [read_tool.description.generate_call()]
    )
    tool_calls = resp[1]
    if not tool_calls:
        return
    conv.push_tool_calls('assistant', tool_calls)
    if not tool_calls:
        return
    for call in tool_calls:
        res = chat.call_tool_native(call)
        conv.push_tool(call.id, call.function.name, str(res))

    msgs = conv.get_messages()
    print(msgs)

    msg, _ = client.ask_with_tools(
            msgs,
            [read_tool.description.generate_call()]
    )
    print(msg[0].text)


if __name__ == "__main__":
    # main()
    test()
