import config
import logging

from multiprocessing import Pool
from trackers.scrappers import Edenor, Edesur, Metrogas
from trackers.scrappers.types import Scrapper, ScrapperReport


__all__ = ["Full"]


logger = logging.getLogger(__name__)


class Full:
    name: str = "Full Tracker"

    def __init__(self):
        self.scrappers: list[Scrapper] = [Edenor(), Edesur(), Metrogas()]

    def run(self) -> list[ScrapperReport]:
        logger.info("begin #run()")

        with Pool(processes=config.SCRAPPER_POOL_SIZE) as pool:
            reports = pool.map(Scrapper.run_report, self.scrappers)

        logger.info("end #run()")
        return sorted(reports, key=lambda x: x.title)

    def run_scrapper(self, scrapper: Scrapper) -> ScrapperReport:
        report = scrapper.run_report()
        return report
