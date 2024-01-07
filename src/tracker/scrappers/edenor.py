from selenium.webdriver.firefox.webdriver import WebDriver
from .types import DebtReport, Scrapper


class Edenor(Scrapper):
    def __init__(self):
        super().__init__("Edenor")

    def scrap(self, driver: WebDriver) -> DebtReport:
        return DebtReport("edenor_id", "Address Edenor", 1000.5)
