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
    def __init__(self):
        super().__init__("Edenor", "https://www.edenordigital.com")

        self.login_credentials = {
            "email": config.EDENOR_EMAIL,
            "password": config.EDENOR_PWD,
        }

    def scrap(self, driver: WebDriver) -> list[DebtReport]:
        base_url = self.link + "/cuentas/resumen"
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

        self.close_popups(driver)

        def find_accounts():
            select_button = driver.find_element(
                "xpath",
                "//div[contains(@class, 'styles_accountSelect')]",
            )
            select_button.click()

            accounts = driver.find_elements(
                "xpath", "//div[contains(@class, 'styles_menuPaper')]//li"
            )
            logger.info("Account cards found")
            return accounts

        accounts = find_accounts()
        account_num = len(accounts)
        logger.info(f"Found {account_num} account card elements")

        if account_num == 0:
            raise Exception("No accounts where found")

        reports = []
        for i in range(account_num):
            logger.info(f"Scrapping account {i}")
            account = accounts[i]

            logger.info("Navigating to account page")
            account.click()

            account_info_container = driver.find_element(
                "xpath",
                "//div[contains(@class, 'styles_cardContent')]/div[contains(@class, 'styles_data')]",
            )

            name = account_info_container.find_element("tag name", "h3").text
            account_info = account_info_container.find_elements(
                "xpath", "./div[contains(@class, 'styles_info')]/*"
            )
            location = account_info[0].text

            address = f"{name}, {location}"
            logger.info(f"Address found: {address}")

            id_match = re.search(r"N°\s+(\d+)\s+-", account_info[1].text)
            if id_match is None:
                raise Exception(f"Account ID could not be found for {address}")

            id = id_match.group(1)
            logger.info(f"ID found: {id}")

            debt_container = driver.find_element(
                "xpath",
                "//div[contains(@class, 'styles_container') and ./h4[text() = 'Estado de cuenta']]",
            )

            debt_integer = debt_container.find_element(
                "xpath", ".//h1[contains(@class, 'styles_amount')]"
            ).text

            debt_decimal = debt_container.find_element(
                "xpath", ".//div[contains(@class, 'styles_decimal')]"
            ).text

            debt = float(
                debt_integer.removeprefix("$").replace(".", "") + "." + debt_decimal
            )
            logger.info(f"Debt found: {debt}")

            logger.info(f"Account {i} scrapping successful: {id}, {address}, {debt}")

            reports.append(DebtReport(id, address, debt))

            accounts = find_accounts()

        return reports

    def close_popups(self, driver):
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
