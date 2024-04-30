import time
import sys
import math
import logging

from trackers.scrappers import Edenor

logging.basicConfig(
    format="[%(asctime)s][%(name)s][%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)


def main():
    start = time.time()
    headless = "--headless" in sys.argv
    crash = "--crash" in sys.argv
    report = Edenor(headless=headless, crash=crash).run_report()
    elapsed_time = time.time() - start
    print("Duracion: ", math.ceil(elapsed_time), "segundos\n")

    print(report.title)

    if report.content is None:
        print("Informacion no disponible.")
        return

    for d in report.content:
        print("-", d.id, d.address, d.debt)


if __name__ == "__main__":
    main()
