import src.config as config

from multiprocessing import Pool
from selenium import webdriver
from selenium.webdriver.firefox.webdriver import WebDriver
from pyeffects.Either import Either
from .types import Scrapper, DebtReport


scrappers: list[Scrapper] = []


def new_driver() -> WebDriver:
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)
    driver.implicitly_wait(config.IMPLICIT_WAIT)
    return driver


def run_report(scrapper: Scrapper) -> Either[DebtReport]:
    return scrapper(new_driver())


def run_reports() -> list[Either[DebtReport]]:
    with Pool(processes=config.SCRAPPER_POOL_SIZE) as pool:
        reports = pool.map(run_report, scrappers)
    return reports
