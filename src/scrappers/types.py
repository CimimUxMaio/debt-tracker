import config
import time
import logging

from abc import ABC, abstractmethod
from typing import NamedTuple
from selenium import webdriver
from selenium.webdriver.firefox.webdriver import WebDriver


logger = logging.getLogger(__name__)


class DebtReport(NamedTuple):
    id: str
    address: str
    debt: float


class ScrapperReport(NamedTuple):
    title: str
    link: str
    content: list[DebtReport] | None


class Scrapper(ABC):
    def __init__(self, name: str, link: str):
        self.name = name
        self.link = link
        self.headless = True
        self.crash = False

    def wait(self):
        time.sleep(config.IMPLICIT_WAIT)

    def run_report(self) -> ScrapperReport:
        options = webdriver.FirefoxOptions()
        if config.FIREFOX_PATH is not None:
            options.binary_location = config.FIREFOX_PATH

        service = webdriver.FirefoxService()
        if config.GECKODRIVER_PATH is not None:
            service.path = config.GECKODRIVER_PATH

        if self.headless:
            options.add_argument("--headless")

        with webdriver.Firefox(service=service, options=options) as driver:
            driver.implicitly_wait(config.IMPLICIT_WAIT)
            try:
                content = self.scrap(driver)
            except Exception as e:
                if self.crash:
                    raise e

                content = None

        return ScrapperReport(self.name, self.link, content)

    @abstractmethod
    def scrap(self, driver: WebDriver) -> list[DebtReport]:
        pass
