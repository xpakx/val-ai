from agent.client import Client, ToolCall, Message, TextMessage
from agent.client.typedefs import OpenAIToolCall
from agent.toolgen import ToolDefinition
from agent.ui import UIProvider
from agent.systemprompt import SystemPromptInformation
from agent.prompt import Prompt
from agent.prompt.signals import signal
from agent.context import Context
from typing import TypeIs


def is_tool_call(val: Message) -> TypeIs[ToolCall]:
    return val.type == 'tool'


def is_text_msg(val: Message) -> TypeIs[TextMessage]:
    return val.type == 'text'


class Chat:
    def __init__(
        self,
        client: Client,
        ui: UIProvider,
        tool_support: bool = False
    ):
        self.client = client
        self.tools: dict[str, ToolDefinition] = {}
        self.conversation = Context()
        self.system_prompt_parts: list[SystemPromptInformation] = []
        self.ui = ui
        self.show_tools = signal(True)
        self.tools_support = tool_support
        self.prepare_prompt()

    def prepare_prompt(self):
        self.prompt = Prompt.from_file("prompts/main.md")
        self.prompt.set_prefix('\n')
        tool_prompt = Prompt.from_file("prompts/tool_desc.md")
        tool_prompt.bind_visibility(self.show_tools)
        self.prompt.add_part(tool_prompt)

        self.info_subprompt = Prompt("")
        for part in self.system_prompt_parts:
            self.info_subprompt.add_part(part)
        self.prompt.add_part(self.info_subprompt)

        if self.tools_support:
            return
        self.tools_subprompt = Prompt("# TOOLS\n")
        self.tools_subprompt.bind_visibility(self.show_tools)
        for tool in self.tools.values():
            self.tools_subprompt.add_part(tool.description)
        self.prompt.add_part(self.tools_subprompt)
        self.show_tools.set(len(self.tools) > 0)

    def get_sys(self):
        self.show_tools.set(len(self.tools) > 0)
        return self.prompt.content()

    def run(self):
        self.conversation.push('system', self.get_sys())
        self.ui.debug(self.conversation.get_messages())
        self.read_user_input = True
        while (True):
            cont = self.step()
            if (not cont):
                break

    def read_input(self):
        user_prompt = self.ui.get_input()
        if (not user_prompt):
            return False
        if (user_prompt in ["quit", "exit"]):
            return False
        self.conversation.push("user", user_prompt)
        return True

    def step(self):
        if (self.read_user_input):
            cont = self.read_input()
            if (not cont):
                return False

        ai = self.client.ask(self.conversation.get_messages())
        self.ui.debug(ai)
        toolResults = []
        for part in ai:
            if is_text_msg(part):
                self.process_text_msg(part)
            else:
                self.process_tool_call(part, toolResults)
        if len(toolResults) == 0:
            self.read_user_input = True
            return True
        self.read_user_input = False

        self.conversation.push(
                "user",
                "\n".join(toolResults)
        )
        self.ui.debug(self.conversation.get_messages())
        return True

    def process_text_msg(self, msg: TextMessage):
        self.conversation.push("assistant", msg.text)
        self.ui.say("Agent", msg.text)

    def process_tool_call(self, call: ToolCall, results: list):
        self.ui.debug('tool call')
        toolResult = self.call_tool(call)
        self.ui.debug(toolResult)
        self.conversation.push(
            "assistant",
            f"tool call: {call.name}, {call.args}"
        )
        results.append(toolResult)

    def add_tool(self, tool: ToolDefinition):
        self.tools[tool.name] = tool
        if self.tools_support:
            return
        self.tools_subprompt.add_part(tool.description)

    def call_tool(self, call: ToolCall):
        tool = self.tools[call.name]
        if not tool:
            return "Error: no such tool"
        try:
            return tool.function(**call.args)
        except Exception:
            return "Error while calling tool"

    def add_system_part(self, part: SystemPromptInformation):
        self.system_prompt_parts.append(part)
        self.info_subprompt.add_part(part)

    def call_tool_native(self, call: OpenAIToolCall):
        tool = self.tools[call.function.name]
        result = ""
        if not tool:
            result = "Error: no such tool"
        try:
            args = tool.description.parse_args(call.function.arguments)
            result = tool.function(**args)
        except Exception:
            result = "Error while calling tool"
        return {
            "role": "tool",
            "tool_call_id": call.id,
            "name": call.function.name,
            "content": result
        }
