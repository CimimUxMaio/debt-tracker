from trackers import ScrapperReport
from typing import NamedTuple, Protocol


class Tracker(Protocol):
    def run(self) -> list[ScrapperReport]:
        ...


class RequestData(NamedTuple):
    chat_id: int
    purpose: str


class ReportRequest(NamedTuple):
    tracker: Tracker
    data: RequestData


class ReportReply(NamedTuple):
    reports: list[ScrapperReport]
    data: RequestData
