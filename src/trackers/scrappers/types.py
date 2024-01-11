import config
import time

from abc import ABC, abstractmethod
from typing import NamedTuple
from selenium import webdriver
from selenium.webdriver.firefox.webdriver import WebDriver


class DebtReport(NamedTuple):
    id: str
    address: str
    debt: float


class ScrapperReport(NamedTuple):
    title: str
    content: list[DebtReport] | None


class Scrapper(ABC):
    def __init__(self, name: str):
        self.name = name

    def wait(self):
        time.sleep(config.IMPLICIT_WAIT)

    def run_report(self) -> ScrapperReport:
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")

        with webdriver.Firefox(options=options) as driver:
            driver.implicitly_wait(config.IMPLICIT_WAIT)
            try:
                content = self.scrap(driver)
            except Exception:
                content = None

        return ScrapperReport(self.name, content)

    @abstractmethod
    def scrap(self, driver: WebDriver) -> list[DebtReport]:
        pass
