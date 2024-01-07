from datetime import datetime
import time
import schedule
import config as config
import multiprocessing as mp

from typing import Tuple
from multiprocessing.pool import Pool
from tracker.scrappers import Edenor, Edesur, Metrogas
from tracker.scrappers.types import Scrapper, ScrapperReport


__all__ = ["DebtTracker"]


def run_scrapper(scrapper: Scrapper) -> ScrapperReport:
    return scrapper.run_report()


class DebtTracker(mp.Process):
    scrappers: list[Scrapper] = [Edenor(), Edesur(), Metrogas()]

    def __init__(self):
        super().__init__()

    def run(self):
        with mp.Pool(processes=config.SCRAPPER_POOL_SIZE) as pool:
            schedule.every(60).seconds.do(self.report_debt, pool)
            while True:
                schedule.run_pending()

                # Sleep until next event
                next_run = schedule.next_run()
                if next_run is not None:
                    next_run_delta = next_run - datetime.now()
                    if next_run_delta.total_seconds() <= 0:
                        continue
                    time.sleep(next_run_delta.total_seconds())

    def report_debt(self, pool: Pool):
        reports = pool.map(run_scrapper, self.scrappers)
        for s, rs in reports:
            print(s)
            for r in rs:
                print(r)
