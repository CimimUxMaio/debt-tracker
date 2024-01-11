from trackers.scrappers import Edenor


def main():
    report = Edenor().run_report()

    print(report.title)

    if report.content is None:
        print("No content")
        return

    for r in report.content:
        print(r)


if __name__ == "__main__":
    main()
