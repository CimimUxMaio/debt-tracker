import config as config

from multiprocessing import Pool
from trackers.scrappers import Edenor, Edesur, Metrogas
from trackers.scrappers.types import Scrapper, ScrapperReport


__all__ = ["Full"]


class Full:
    name: str = "Full Tracker"

    def __init__(self):
        self.scrappers: list[Scrapper] = [Edenor(), Edesur(), Metrogas()]

    def run(self) -> list[ScrapperReport]:
        with Pool(processes=config.SCRAPPER_POOL_SIZE) as pool:
            reports = pool.map(Scrapper.run_report, self.scrappers)
        return reports
