import logging
import sys
import time
import math

from scrappers.types import Scrapper


def run(scrapper: Scrapper):
    headless = "--headless" in sys.argv
    crash = "--crash" in sys.argv

    log_level = logging.INFO
    if "--debug" in sys.argv:
        log_level = logging.DEBUG

    logging.basicConfig(
        format="[%(asctime)s][%(name)s][%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
        level=log_level,
    )

    scrapper.headless = headless
    scrapper.crash = crash

    start = time.time()
    report = scrapper.run_report()
    elapsed_time = time.time() - start

    print()
    print("Tiempo de ejecución: ", math.ceil(elapsed_time), "segundos\n")

    print(report.title)

    if report.content is None:
        print("Informacion no disponible.")
        return

    for d in report.content:
        print(f"- {d.id}, {d.address}:  $ {d.debt}")
