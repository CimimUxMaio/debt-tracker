from trackers.scrappers.types import ScrapperReport, DebtReport


class Dummy:
    """Dummy tracker for testing"""

    def run(self) -> list[ScrapperReport]:
        """Returns some dummy scrapper reports"""
        return [
            (
                f"Dummy Scrapper {n}",
                [DebtReport(str(i), f"Address {i}", i * 100.3) for i in range(3)],
            )
            for n in range(3)
        ]
