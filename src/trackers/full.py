import config as config
import multiprocessing as mp

from trackers.scrappers import Edenor, Edesur, Metrogas
from trackers.scrappers.types import Scrapper, ScrapperReport


__all__ = ["Full"]


class Full:
    name: str = "Full Tracker"
    scrappers: list[Scrapper] = [Edenor(), Edesur(), Metrogas()]

    def run_scrapper(self, scrapper: Scrapper) -> ScrapperReport:
        return scrapper.run_report()

    def run(self) -> list[ScrapperReport]:
        with mp.Pool(processes=config.SCRAPPER_POOL_SIZE) as pool:
            reports = pool.map(self.run_scrapper, self.scrappers)
        return reports
