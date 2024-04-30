import config
import logging
import re

from selenium.common.exceptions import (
    ElementClickInterceptedException,
)
from selenium.webdriver.firefox.webdriver import WebDriver
from .types import DebtReport, Scrapper

logger = logging.getLogger(__name__)


class Edenor(Scrapper):
    def __init__(self, *, headless: bool = True, crash: bool = False):
        super().__init__(
            "Edenor",
            "https://www.edenordigital.com",
            headless=headless,
            crash=crash,
        )

        self.login_credentials = {
            "email": config.EDENOR_EMAIL,
            "password": config.EDENOR_PWD,
        }

    def scrap(self, driver: WebDriver) -> list[DebtReport]:
        base_url = self.link + "/cuentas"
        logger.info(f"Navigating to: {base_url}")
        driver.get(base_url)

        email_input = driver.find_element(
            "xpath",
            "//input[@type='text']",
        )
        password_input = driver.find_element(
            "xpath",
            "//input[@type='password']",
        )
        submit_button = driver.find_element(
            "xpath", "//button[.//div[contains(text(), 'Ingresar')]]"
        )

        logger.info("Log in elements found")

        email_input.send_keys(self.login_credentials["email"])
        password_input.send_keys(self.login_credentials["password"])
        submit_button.click()

        logger.info("Log in successful")

        # Handle popups that were hidden
        logger.info("Waiting for popups to load")
        self.wait()
        popups = driver.find_elements("xpath", "//div[@role = 'dialog']")
        popup_close_btns = [
            popup.find_element("xpath", ".//button[1]") for popup in popups
        ]
        attempt = 0
        while len(popup_close_btns) > 0:
            try:
                popup_close_btns[attempt].click()
                popup_close_btns.pop(attempt)
                attempt = 0
            except ElementClickInterceptedException:
                attempt += 1

        logger.info("Popups successfully closed")

        def find_cards():
            cards = driver.find_elements(
                "xpath",
                "//div[contains(@class, 'styles_container')]//div[contains(@class, 'styles_row')]/div[contains(@class, 'styles_item')]",
            )
            logger.info("Account cards found")
            return cards

        account_cards = find_cards()
        account_num = len(account_cards)
        logger.info(f"Found {account_num} account card elements")

        if account_num == 0:
            raise Exception("No accounts where found")

        reports = []
        for i in range(account_num):
            logger.info(f"Scrapping account {i}")
            card = account_cards[i]

            header = card.find_elements(
                "xpath", ".//div[contains(@class, 'styles_accountAddress')]/*"
            )

            address = f"{header[0].text}, {header[1].text}"
            logger.info(f"Address found: {address}")

            info = card.find_element(
                "xpath", ".//div[contains(@class, 'styles_accountInfo')]/div"
            )

            id_match = re.search(r"Cuenta N°\s+(\d+)\s+-", info.text)
            if id_match is None:
                raise Exception(f"Account ID could not be found for {address}")

            id = id_match.group(1)

            logger.info(f"ID found: {id}")

            logger.info("Navigating to account page")
            card.click()

            debt_integer = driver.find_element(
                "xpath", "//h1[contains(@class, 'styles_amount')]"
            ).text

            debt_decimal = driver.find_element(
                "xpath", "//div[contains(@class, 'styles_decimal')]"
            ).text

            debt = float(
                debt_integer.removeprefix("$").replace(".", "") + "." + debt_decimal
            )
            logger.info(f"Debt found: {debt}")

            logger.info(f"Account {i} scrapping successful: {id}, {address}, {debt}")

            reports.append(DebtReport(id, address, debt))

            driver.back()

            account_cards = find_cards()

        return reports
