import time
import logging
import config

from typing import NamedTuple
from multiprocessing import Pool
from reporter.types import ReportReply, ReportRequest
from multiprocessing import Queue
from scrappers import Metrogas, Edenor, Edesur
from scrappers.types import ScrapperReport, Scrapper


__all__ = ["Reporter"]


logger = logging.getLogger(__name__)


class CacheItem(NamedTuple):
    report: ScrapperReport
    timestamp: float


class Cache:
    def __init__(self):
        self._dict: dict[str, CacheItem] = {}

    def lookup(self, name: str) -> ScrapperReport | None:
        hit = self._dict.get(name, None)
        if hit is not None and time.time() < hit.timestamp + config.CACHE_LIFETIME * 60:
            logger.info(f"Cache hit for {name}")
            return hit.report

        logger.info(f"Cache miss for {name}")
        return None

    def update(self, name: str, report: ScrapperReport):
        self._dict[name] = CacheItem(report, time.time())
        logger.info(f"Cache updated for {name}")


class Reporter:
    scrappers: list[Scrapper] = [Edenor(), Edesur(), Metrogas()]
    cache: Cache = Cache()

    def run(
        self, request_queue: "Queue[ReportRequest]", reply_queue: "Queue[ReportReply]"
    ):
        while True:
            request = request_queue.get()
            logger.info(f"Received request: {request}")

            # Get scrappers which do not have a caché hit
            scrappers_to_run = []
            cached_reports = []
            for scrapper in self.scrappers:
                if hit := self.cache.lookup(scrapper.name):
                    cached_reports.append(hit)
                else:
                    scrappers_to_run.append(scrapper)

            # Run scrappers in parallel
            with Pool(processes=config.SCRAPPER_POOL_SIZE) as pool:
                results = pool.map(run_scrapper, scrappers_to_run)

            # Update cache with the newly generated reports
            new_reports = []
            for scrapper, report in results:
                self.cache.update(scrapper.name, report)
                new_reports.append(report)

            reports = cached_reports + new_reports

            # Queue reply
            reply_queue.put_nowait(ReportReply(reports, request))


def run_scrapper(scrapper: Scrapper) -> tuple[Scrapper, ScrapperReport]:
    logger.info(f"Running scrapper: {scrapper.name}")

    report = scrapper.run_report()

    if report.content is None:
        logger.warn("Scrapped content is missing")

    logger.info(f"Scrapper {scrapper.name} finished")
    return scrapper, report
