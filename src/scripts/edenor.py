import time
import math

from trackers.scrappers import Edenor


def main():
    start = time.time()
    report = Edenor(headless=False, crash=True).run_report()
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
