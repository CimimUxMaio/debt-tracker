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
    def __init__(self, name: str, *, headless: bool = True, crash: bool = False):
        self.name = name
        self.headless = headless
        self.crash = crash

    def wait(self):
        time.sleep(config.IMPLICIT_WAIT)

    def run_report(self) -> ScrapperReport:
        options = webdriver.FirefoxOptions()
        if self.headless:
            options.add_argument("--headless")

        with webdriver.Firefox(options=options) as driver:
            driver.implicitly_wait(config.IMPLICIT_WAIT)
            try:
                content = self.scrap(driver)
            except Exception as e:
                if self.crash:
                    raise e

                content = None

        return ScrapperReport(self.name, content)

    @abstractmethod
    def scrap(self, driver: WebDriver) -> list[DebtReport]:
        pass
