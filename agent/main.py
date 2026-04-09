from config import load_config
from client import Client, ChatMessage, ToolCall
from typing import Callable
from toolgen import get_tool, ToolDefinition


class Chat:
    def __init__(self, client: Client, get_input: Callable):
        self.client = client
        self.get_input = get_input
        self.tools: dict[str, ToolDefinition] = {}
        self.conversation: list[ChatMessage] = []

    def get_sys(self):
        t = """all responses must be valid json list.
            each element would have 'type' field.
            if type is text, then element represents
            message for user, and the message itself would be
            in text field.
            """
        if len(self.tools) > 0:
            t = t + """if type is tool, then element represents
            tool call and field 'args' must follow tool's schema
            and 'name' field tool's name
            """
        for tool in self.tools.values():
            t += tool.description.content()

        return t

    def run(self):
        self.conversation = []
        self.conversation.append({
            "role": "system",
            "content": self.get_sys()

        })
        print(self.conversation)
        self.read_user_input = True
        while (True):
            cont = self.step()
            if (not cont):
                break

    def read_input(self):
        user_prompt = self.get_input()
        if (not user_prompt):
            return False
        if (user_prompt in ["quit", "exit"]):
            return False
        self.conversation.append({"role": "user", "content": user_prompt})
        return True

    def step(self):
        if (self.read_user_input):
            cont = self.read_input()
            if (not cont):
                return False

        ai = self.client.ask(self.conversation)
        print(ai)
        toolResults = []
        for part in ai:
            if part.type == 'text':
                self.conversation.append({
                    "role": "assistant",
                    "content": part.text
                })
                print(part.text)
            if part.type == 'tool':
                print('tool call')
                toolResult = self.call_tool(part)
                print(toolResult)
                self.conversation.append({
                    "role": "assistant",
                    "content": f"tool call: {part.name}, {part.args}"
                })
                toolResults.append(toolResult)
        if len(toolResults) == 0:
            self.read_user_input = True
            return True
        self.read_user_input = False

        self.conversation.append(
                {"role": "user",
                 "content": "\n".join(toolResults)}
        )
        print(self.conversation)
        return True

    def add_tool(self, tool: ToolDefinition):
        self.tools[tool.name] = tool

    def call_tool(self, call: ToolCall):
        tool = self.tools[call.name]
        if not tool:
            return "Error: no such tool"
        return tool.function(**call.args)


def get_weather(city: str) -> dict:
    """
    Fetches the current weather for a specific city.
    """
    if "london" in city.lower():
        return "15°C and cloudy"
    return "22°C and sunny"


def main():
    print("Hello from VAL-ai!")
    config = load_config("data/config.json")
    client = Client(config)
    chat = Chat(client, input)
    weather = get_tool(get_weather)
    chat.add_tool(weather)

    chat.run()


if __name__ == "__main__":
    main()
