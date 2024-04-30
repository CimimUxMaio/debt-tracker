import config
import logging

from selenium.webdriver.firefox.webdriver import WebDriver
from .types import DebtReport, Scrapper


logger = logging.getLogger(__name__)


class Metrogas(Scrapper):
    def __init__(self, *, headless: bool = True, crash: bool = False):
        super().__init__(
            "Metrogas",
            "https://registro.micuenta.metrogas.com.ar/",
            headless=headless,
            crash=crash,
        )

        self.login_credentials = {
            "email": config.METROGAS_EMAIL,
            "password": config.METROGAS_PWD,
        }

    def scrap(self, driver: WebDriver) -> list[DebtReport]:
        logger.info(f"Navigating to: {self.link}")
        driver.get(self.link)

        login_button = driver.find_element("id", "loginButton")
        logger.info("Login button found")
        login_button.click()
        logger.info("Navigating to login page")

        logger.info("Waiting for login page to load")
        self.wait()

        email_input = driver.find_element("id", "j_username")
        password_input = driver.find_element("id", "j_password")
        submit_button = driver.find_element("id", "logOnFormSubmit")

        logger.info("Login elements found")

        email_input.send_keys(self.login_credentials["email"])
        password_input.send_keys(self.login_credentials["password"])
        submit_button.click()

        logger.info("Login successful")

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

            logger.info("Account list found")
            return account_list

        account_list = get_account_list()
        account_num = len(account_list)
        logger.info(f"Found {account_num} account elements")

        if account_num == 0:
            raise Exception("No accounts where found")

        reports = []
        for i in range(account_num):
            logger.info(f"Scrapping account {i}")
            account = account_list[i]

            logger.info("Navigating to account page")
            account.click()

            logger.info("Waiting for account info to load")
            self.wait()  # Wait for account info to load

            id = driver.find_element(
                "xpath",
                "//div[./div/span[text() = 'Número de Cliente']]/div[2]//span",
            ).text

            logger.info(f"ID found: {id}")

            address = driver.find_element(
                "xpath",
                "//div[./div/span[text() = 'Dirección']]/div[2]//span",
            ).text
            logger.info(f"Address found: {address}")

            debt_text = driver.find_element(
                "xpath",
                "//div[./div/div[text() = 'Estado de Cuenta']]//span[contains(text(), '$') or text() = 'No registra deuda']",
            ).text

            logger.info("Debt elements found")

            debt = 0
            if debt_text != "No registra deuda":
                debt = float(
                    debt_text.removeprefix("$")
                    .strip()
                    .replace(".", "")
                    .replace(",", ".")
                )

            logger.info(f"Debt found: {debt}")

            logger.info(f"Account {i} scrapping successful: {id}, {address}, {debt}")

            reports.append(DebtReport(id, address, debt))

            account_list = get_account_list()

        return reports
