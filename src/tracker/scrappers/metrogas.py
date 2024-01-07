from selenium.webdriver.firefox.webdriver import WebDriver
from .types import DebtReport, Scrapper


class Metrogas(Scrapper):
    def __init__(self):
        super().__init__("Metrogas")

    def scrap(self, driver: WebDriver) -> DebtReport:
        return DebtReport("metrogas_id", "Address metrogas", 333.5)
