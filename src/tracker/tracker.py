import time
import schedule
import config as config

from multiprocessing import Pool, Process
from tracker.scrappers import Edenor, Edesur, Metrogas
from tracker.scrappers.types import Scrapper, DebtReport


__all__ = ["DebtTracker"]


def run_scrapper(scrapper: Scrapper):
    return scrapper.run_report()


class DebtTracker(Process):
    scrappers: list[Scrapper] = [Edenor(), Edesur(), Metrogas()]

    def __init__(self):
        super().__init__()

    def run(self):
        schedule.every(5).seconds.do(self.run_reports)
        while True:
            schedule.run_pending()
            time.sleep(1)

    def run_reports(self) -> list[DebtReport]:
        with Pool(processes=config.SCRAPPER_POOL_SIZE) as pool:
            reports = pool.map(run_scrapper, self.scrappers)
        print(reports)
        return reports
