from config import load_config
from client import Client, ChatMessage


class Chat:
    def __init__(self, client, get_input):
        self.client = client
        self.get_input = get_input
        self.tools = {}
        self.conversation: list[ChatMessage] = []

    def get_sys(self):
        t = """all responses must be valid json list.
            each element would have 'type' field.
            if type is text, then element represents
            message for user, and the message itself would be
            in text field.
            """
        return t

    def run(self):
        self.conversation = []
        self.conversation.append({
            "role": "system",
            "content": self.get_sys()

        })
        while (True):
            cont = self.step()
            if (not cont):
                break

    def step(self):
        user_prompt = self.get_input()
        if (not user_prompt):
            return False
        if (user_prompt in ["quit", "exit"]):
            return False
        self.conversation.append({"role": "user", "content": user_prompt})

        ai = self.client.ask(self.conversation)
        print(ai)
        for part in ai:
            if part.type == 'text':
                self.conversation.append({
                    "role": "assistant",
                    "content": part.text
                })
                print(part.text)
        return True


def main():
    print("Hello from VAL-ai!")
    config = load_config("data/config.json")
    client = Client(config)
    chat = Chat(client, input)
    chat.run()


if __name__ == "__main__":
    main()
