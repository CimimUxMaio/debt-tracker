from reporter.types import ReportReply, ReportRequest
from multiprocessing import Queue

__all__ = ["Reporter"]


class Reporter:
    def __init__(
        self, request_queue: "Queue[ReportRequest]", reply_queue: "Queue[ReportReply]"
    ):
        self.request_queue = request_queue
        self.reply_queue = reply_queue

    def run(self):
        while True:
            request = self.request_queue.get()
            reports = request.tracker.run()
            self.reply_queue.put_nowait(ReportReply(reports, request.data))
