import time
import logging
import config

from typing import NamedTuple
from reporter.types import ReportReply, ReportRequest
from multiprocessing import Queue
from trackers.scrappers.types import ScrapperReport


__all__ = ["Reporter"]


logger = logging.getLogger(__name__)


class CacheItem(NamedTuple):
    reports: list[ScrapperReport]
    timestamp: float


Cache = dict[str, CacheItem]


class Reporter:
    def __init__(
        self, request_queue: "Queue[ReportRequest]", reply_queue: "Queue[ReportReply]"
    ):
        self.request_queue = request_queue
        self.reply_queue = reply_queue
        self._cache: Cache = {}

    def run(self):
        while True:
            request = self.request_queue.get()
            logger.info(f"Received request for tracker: {request.tracker.name}")

            hit = self.cache_hit(request.tracker.name)
            if hit is None:
                reports = request.tracker.run()
                self.update_cache(request.tracker.name, reports)
            else:
                logger.info(f"Cache hit for tracker: {request.tracker.name}")
                reports = hit.reports

            self.reply_queue.put_nowait(ReportReply(reports, request.data))

    def update_cache(self, tracker: str, reports: list[ScrapperReport]):
        if any([report.content is None for report in reports]):
            return

        logger.info(f"Updating cache for tracker: {tracker}")
        self._cache[tracker] = CacheItem(reports, time.time())

    def cache_hit(self, tracker: str) -> CacheItem | None:
        hit = self._cache.get(tracker, None)
        if hit is not None and time.time() < hit.timestamp + config.CACHE_LIFETIME * 60:
            return hit
        return None
