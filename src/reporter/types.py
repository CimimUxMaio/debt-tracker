from scrappers.types import ScrapperReport
from typing import NamedTuple


class ReportRequest(NamedTuple):
    chat_ids: list[int]
    purpose: str


class ReportReply(NamedTuple):
    reports: list[ScrapperReport]
    request: ReportRequest
