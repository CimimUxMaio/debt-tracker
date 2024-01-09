import os

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
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
            "/html/body/div[1]/div/div[1]/div[1]/div/div[1]/div/form/div/div[1]/div/div[1]/div/div/input",
        )
        password_input = driver.find_element(
            "xpath",
            "/html/body/div[1]/div/div[1]/div[1]/div/div[1]/div/form/div/div[2]/div/div[1]/div/div/div/input",
        )
        submit_button = driver.find_element(
            "xpath", "/html/body/div[1]/div/div[1]/div[1]/div/div[1]/div/button/span[1]"
        )

        email_input.send_keys(self.login_credentials["email"])
        password_input.send_keys(self.login_credentials["password"])
        submit_button.click()

        # Repeated to handle unpredictable order
        popups_selectors = [
            ".c0014",
            ".styles_closeButton__3IxJb",
        ]

        hidden_popups_selectors = []
        for popup in popups_selectors:
            print("Handling popup:", popup, "...")
            try:
                popup_close_button = driver.find_element("css selector", popup)
                popup_close_button.click()
            except NoSuchElementException:
                print("No popup found")
            except ElementClickInterceptedException:
                print("Popup is hidden")
                hidden_popups_selectors.append(popup)

        # Handle popups that were hidden
        for popup in hidden_popups_selectors:
            popup_close_button = driver.find_element("css selector", popup)
            popup_close_button.click()

        grid_display_button = driver.find_element(
            "xpath",
            "/html/body/div[1]/div/div[2]/div[2]/div[1]/div[2]/div/div/div[2]/div/div/button[3]",
        )
        grid_display_button.click()

        account_registers = driver.find_elements(
            "css selector", "div.styles_responsiveRow__316me"
        )

        register_num = len(account_registers)

        reports = []
        for i in range(register_num):
            account_register = account_registers[i]
            account_data = account_register.find_elements("tag name", "span")
            address = account_data[0].text
            id = account_data[1].text

            view_details_button = account_register.find_element("tag name", "button")
            view_details_button.click()

            debt_integer = driver.find_element(
                "css selector", ".styles_amount__11Aff"
            ).text
            debt_decimal = driver.find_element(
                "css selector", ".styles_decimal__1DINq"
            ).text
            debt = float(
                debt_integer.removeprefix("$").replace(".", "") + "." + debt_decimal
            )

            reports.append(DebtReport(id, address, debt))
            driver.back()
            account_registers = driver.find_elements(
                "css selector", "div.styles_responsiveRow__316me"
            )
        return reports
