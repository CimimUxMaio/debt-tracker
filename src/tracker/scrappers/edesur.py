from selenium.webdriver.firefox.webdriver import WebDriver
from .types import DebtReport, Scrapper


class Edesur(Scrapper):
    def __init__(self):
        super().__init__("Edesur")

    def scrap(self, driver: WebDriver) -> DebtReport:
        return DebtReport("edesur_id", "Address Edesur", 500.5)
