from agent.client import Client
from agent.prompt import Prompt
from agent.context import Context


class HelperWorker:
    def __init__(
        self,
        client: Client,
        prompt: Prompt
    ):
        self.client = client
        self.prompt = prompt
        self.context = Context()
        self.context.push('system', self.prompt)
        self.context.freeze()

    def ask(self, msg: str):
        self.context.push('user', msg)
        conversation = self.context.get_messages()
        response = self.client.ask(conversation)
        self.context.reset()
        return response
