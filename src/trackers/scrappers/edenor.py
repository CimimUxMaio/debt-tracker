import os
import time
import config

from selenium.common.exceptions import (
    ElementClickInterceptedException,
)
from selenium.webdriver.firefox.webdriver import WebDriver
from .types import DebtReport, Scrapper


class Edenor(Scrapper):
    login_url = "https://www.edenordigital.com/ingreso"

    login_credentials = {
        "email": os.getenv("EDENOR_EMAIL"),
        "password": os.getenv("EDENOR_PWD"),
    }

    def __init__(self):
        super().__init__("Edenor")

    def scrap(self, driver: WebDriver) -> list[DebtReport]:
        driver.get(self.login_url)

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

        email_input.send_keys(self.login_credentials["email"])
        password_input.send_keys(self.login_credentials["password"])
        submit_button.click()

        # Handle popups that were hidden
        time.sleep(config.IMPLICIT_WAIT)
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

        grid_display_button = driver.find_element(
            "xpath", "//button[.//*[local-name()='svg' and @width='21px']]"
        )
        grid_display_button.click()

        account_registers = driver.find_elements(
            "xpath", "//div[contains(@class, 'styles_responsiveRow')]"
        )

        register_num = len(account_registers)

        reports = []
        for i in range(register_num):
            account_register = account_registers[i]
            account_data = account_register.find_elements("tag name", "span")
            address = account_data[0].text
            id = account_data[1].text

            view_details_button = account_register.find_element(
                "xpath", "(.//div[@role='button'])[2]"
            )
            view_details_button.click()

            debt_integer = driver.find_element(
                "xpath", "//h1[contains(@class, 'styles_amount')]"
            ).text

            debt_decimal = driver.find_element(
                "xpath", "//div[contains(@class, 'styles_decimal')]"
            ).text

            debt = float(
                debt_integer.removeprefix("$").replace(".", "") + "." + debt_decimal
            )

            reports.append(DebtReport(id, address, debt))

            driver.back()

            account_registers = driver.find_elements(
                "xpath", "//div[contains(@class, 'styles_responsiveRow')]"
            )

        return reports
