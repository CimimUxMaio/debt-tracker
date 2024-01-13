import os

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.firefox.webdriver import WebDriver
from .types import DebtReport, Scrapper


class Edesur(Scrapper):
    login_url = "https://ov.edesur.com.ar/login"

    login_credentials = {
        "email": os.getenv("EDESUR_EMAIL"),
        "password": os.getenv("EDESUR_PWD"),
    }

    def __init__(self, *, headless: bool = True, crash: bool = False):
        super().__init__("Edesur", headless=headless, crash=crash)

    def scrap(self, driver: WebDriver) -> list[DebtReport]:
        driver.get(self.login_url)

        email_input = driver.find_element(
            "xpath",
            "//input[@type = 'email']",
        )
        password_input = driver.find_element(
            "xpath",
            "//input[@type = 'password']",
        )
        submit_button = driver.find_element(
            "xpath",
            "//button[text() = 'Ingresar']",
        )

        email_input.send_keys(self.login_credentials["email"])
        password_input.send_keys(self.login_credentials["password"])
        submit_button.click()

        def get_account_list(*, wait=False):
            account_list_button = driver.find_element(
                "xpath", "//selector-account//button"
            )
            driver.execute_script("arguments[0].click();", account_list_button)

            if wait:
                self.wait()  # Wait for list to load

            account_list = driver.find_elements(
                "xpath", "//selector-account//div[@class = 'mt-1 scroll-y-25']/div"
            )

            return account_list

        account_list = get_account_list(wait=True)

        reports = []
        for i in range(len(account_list)):
            account = account_list[i]
            account.click()

            self.wait()  # Wait for account info to load

            account_data = driver.find_elements("tag name", "td")
            id = account_data[2].text
            address = account_data[1].text

            debt_panel = driver.find_element(
                "xpath",
                "//div[./h5[text() = 'Estado de cuenta']]",
            )

            debt_text = debt_panel.find_element(
                "xpath",
                ".//div[./p[text() = 'TOTAL A PAGAR']]/p[2] | .//span[contains(text(), 'no posee deuda')]",
            ).text

            debt = 0
            if debt_text != "Al día de la fecha, su cuenta no posee deuda.":
                debt = float(
                    debt_text.removeprefix("$")
                    .strip()
                    .replace(".", "")
                    .replace(",", ".")
                )

            reports.append(DebtReport(id, address, debt))
            account_list = get_account_list()

        return reports
