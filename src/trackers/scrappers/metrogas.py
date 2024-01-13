import os

from selenium.webdriver.firefox.webdriver import WebDriver
from .types import DebtReport, Scrapper


class Metrogas(Scrapper):
    login_url = "https://registro.micuenta.metrogas.com.ar/"

    login_credentials = {
        "email": os.getenv("METROGAS_EMAIL"),
        "password": os.getenv("METROGAS_PWD"),
    }

    def __init__(self, *, headless: bool = True, crash: bool = False):
        super().__init__("Metrogas", headless=headless, crash=crash)

    def scrap(self, driver: WebDriver) -> list[DebtReport]:
        driver.get(self.login_url)

        login_button = driver.find_element("id", "loginButton")
        login_button.click()

        self.wait()

        email_input = driver.find_element("id", "j_username")
        password_input = driver.find_element("id", "j_password")
        submit_button = driver.find_element("id", "logOnFormSubmit")

        email_input.send_keys(self.login_credentials["email"])
        password_input.send_keys(self.login_credentials["password"])
        submit_button.click()

        def get_account_list():
            account_list_button = driver.find_element(
                "xpath", "//button[.//bdi[text() = 'Cambiar']]"
            )
            account_list_button.click()

            self.wait()  # Wait for list to laod

            account_list = driver.find_elements(
                "xpath",
                "//div[.//span[contains(text(), 'Seleccioná el Número de Cliente')]]//li",
            )

            return account_list

        account_list = get_account_list()

        reports = []
        for i in range(len(account_list)):
            account = account_list[i]
            account.click()

            self.wait()  # Wait for account info to load

            id = driver.find_element(
                "xpath",
                "//div[./div/span[text() = 'Número de Cliente']]/div[2]//span",
            ).text

            address = driver.find_element(
                "xpath",
                "//div[./div/span[text() = 'Dirección']]/div[2]//span",
            ).text

            debt_text = driver.find_element(
                "xpath",
                "//div[./div/div[text() = 'Estado de Cuenta']]//span[contains(text(), '$') or text() = 'No registra deuda']",
            ).text

            debt = 0
            if debt_text != "No registra deuda":
                debt = float(
                    debt_text.removeprefix("$")
                    .strip()
                    .replace(".", "")
                    .replace(",", ".")
                )

            reports.append(DebtReport(id, address, debt))

            account_list = get_account_list()

        return reports
