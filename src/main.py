import os

from dotenv import load_dotenv
from tracker import DebtTracker


load_dotenv()


if __name__ == "__main__":
    token = os.getenv("TELEGRAM_TOKEN")
    if token is None:
        raise Exception("TELEGRAM_TOKEN is not set")

    tracker = DebtTracker()
    tracker.start()
    tracker.join()
