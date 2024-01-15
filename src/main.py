import os
import logging
import multiprocessing as mp

from reporter import Reporter
from telegrambot import TelegramBot
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(
    format="[%(asctime)s][%(name)s][%(levelname)s] %(message)s", level=logging.INFO
)

if __name__ == "__main__":
    mp.set_start_method("spawn")

    token = os.getenv("TELEGRAM_TOKEN")
    if token is None:
        raise Exception("TELEGRAM_TOKEN is not set")

    request_queue = mp.Queue()
    reply_queue = mp.Queue()

    bot = TelegramBot(request_queue, reply_queue)
    p_bot = mp.Process(target=bot.run, args=(token,))

    reporter = Reporter(request_queue, reply_queue)
    p_reporter = mp.Process(target=reporter.run)

    p_reporter.start()
    p_bot.start()

    p_bot.join()
    p_reporter.join()
