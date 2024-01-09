import os
import telegrambot

from dotenv import load_dotenv


load_dotenv()


if __name__ == "__main__":
    token = os.getenv("TELEGRAM_TOKEN")
    if token is None:
        raise Exception("TELEGRAM_TOKEN is not set")

    telegrambot.run(token)
