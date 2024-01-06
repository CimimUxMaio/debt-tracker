from typing import Callable, NamedTuple
from pyeffects.Either import Either
from selenium.webdriver.firefox.webdriver import WebDriver


class DebtReport(NamedTuple):
    id: str
    address: str
    debt: float


Scrapper = Callable[[WebDriver], Either[DebtReport]]
