import config

from abc import ABC, abstractmethod
from typing import NamedTuple, Tuple
from selenium import webdriver
from selenium.webdriver.firefox.webdriver import WebDriver


class DebtReport(NamedTuple):
    id: str
    address: str
    debt: float


ScrapperReport = Tuple[str, list[DebtReport]]


class Scrapper(ABC):
    def __init__(self, name: str):
        self.name = name

    def run_report(self) -> ScrapperReport:
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")

        with webdriver.Firefox(options=options) as driver:
            driver.implicitly_wait(config.IMPLICIT_WAIT)
            try:
                report = self.scrap(driver)
            except Exception:
                report = []

        return self.name, report

    @abstractmethod
    def scrap(self, driver: WebDriver) -> list[DebtReport]:
        pass
