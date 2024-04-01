import time
import math
import sys

from trackers.scrappers import Metrogas


def main():
    start = time.time()
    headless = "--headless" in sys.argv
    crash = "--crash" in sys.argv
    report = Metrogas(headless=headless, crash=crash).run_report()
    elapsed_time = time.time() - start
    print("Duracion: ", math.ceil(elapsed_time), "segundos\n")

    print(report.title)

    if report.content is None:
        print("Informacion no Disponible.")
        return

    for d in report.content:
        print("-", d.id, d.address, d.debt)


if __name__ == "__main__":
    main()
