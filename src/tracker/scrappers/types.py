import config

from abc import ABC, abstractmethod
from typing import NamedTuple
from selenium import webdriver
from selenium.webdriver.firefox.webdriver import WebDriver


class DebtReport(NamedTuple):
    id: str
    address: str
    debt: float


class Scrapper(ABC):
    def __init__(self, name: str):
        self.name = name

    def run_report(self) -> DebtReport:
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")

        with webdriver.Firefox(options=options) as driver:
            driver.implicitly_wait(config.IMPLICIT_WAIT)
            report = self.scrap(driver)

        return report

    @abstractmethod
    def scrap(self, driver: WebDriver) -> DebtReport:
        pass
