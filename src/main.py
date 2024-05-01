import logging
import multiprocessing as mp
import config

from reporter import Reporter
from telegrambot import TelegramBot


logging.basicConfig(
    format="[%(asctime)s][%(name)s][%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)

logging.getLogger("httpx").setLevel(logging.WARNING)

if __name__ == "__main__":
    mp.set_start_method("spawn")

    token = config.TELEGRAM_TOKEN

    request_queue = mp.Queue()
    reply_queue = mp.Queue()

    bot = TelegramBot(request_queue, reply_queue)
    p_bot = mp.Process(target=bot.run, args=(token,))

    reporter = Reporter()
    p_reporter = mp.Process(target=reporter.run, args=(request_queue, reply_queue))

    p_reporter.start()
    p_bot.start()

    p_bot.join()
    p_reporter.join()
