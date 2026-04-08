from config import load_config
from client import Client


def main():
    print("Hello from VAL-ai!")
    config = load_config("data/config.json")
    client = Client(config)
    print(client.ask([{"role": "user", "content": "Hello!"}]))


if __name__ == "__main__":
    main()
