from agent.config import load_config
from agent.client import Client
from agent.toolgen import get_tool
from agent.ui import CLIProvider
from agent.tools import read_file, list_files, write_file, glob_files
from agent.systemparts import current_time
from agent.systemprompt import get_system_prompt_info
from agent.client.backoff import fibonacci_backoff
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
    client = Client(config, fibonacci_backoff)
    chat = Chat(client, CLIProvider())
    prepare_tools(chat)
    conv = Context()
    conv.push('user', 'could you tell me what is in the Makefile?')
    read_tool = get_tool(read_file)
    tool = {
            'type': 'function',
            'function': {
                'name': read_tool.name,
                'description': 'Reads the file on filesystem in a folder agent runs in',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'path': {
                            'type': 'string',
                            'description': 'path to file'
                        }
                    },
                    'required': ['path']
                }
            }
    }
    client.call_api_with_tools(
            conv.get_messages(),
            [tool]
    )


if __name__ == "__main__":
    # main()
    test()
