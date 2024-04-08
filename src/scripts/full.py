import time
import math

from trackers import Full


def main():
    start = time.time()
    reports = Full().run()
    elapsed_time = time.time() - start
    print("Duracion: ", math.ceil(elapsed_time), "segundos\n")

    for r in reports:
        print(r.title)

        if r.content is None:
            print("Informacion no disponible.")
            print("\n")
            continue

        for d in r.content:
            print("-", d.id, d.address, d.debt)

        print("\n")


if __name__ == "__main__":
    main()
