import config
import logging

from selenium.webdriver.firefox.webdriver import WebDriver
from .types import DebtReport, Scrapper

logger = logging.getLogger(__name__)


class Edesur(Scrapper):
    def __init__(self, *, headless: bool = True, crash: bool = False):
        super().__init__(
            "Edesur", "https://ov.edesur.com.ar", headless=headless, crash=crash
        )

        self.login_credentials = {
            "email": config.EDESUR_EMAIL,
            "password": config.EDESUR_PWD,
        }

    def scrap(self, driver: WebDriver) -> list[DebtReport]:
        base_url = f"{self.link}/login"
        logger.info(f"Navigating to: {base_url}")
        driver.get(base_url)

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

        logger.info("Log in elements found")

        email_input.send_keys(self.login_credentials["email"])
        password_input.send_keys(self.login_credentials["password"])
        submit_button.click()

        logger.info("Log in successful")

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

            logger.info("Account list found")
            return account_list

        account_list = get_account_list(wait=True)

        account_num = len(account_list)
        logger.info(f"Found {account_num} account elements")

        if account_num == 0:
            raise Exception("No accounts where found")

        reports = []
        for i in range(account_num):
            account = account_list[i]
            logger.info(f"Scrapping account {i}")

            logger.info("Navigating to account page")
            account.click()

            logger.info("Waiting for account info to load")
            self.wait()  # Wait for account info to load

            account_data = driver.find_elements("tag name", "td")

            id = account_data[2].text
            logger.info(f"ID found: {id}")

            address = account_data[1].text
            logger.info(f"Address found: {address}")

            debt_panel = driver.find_element(
                "xpath",
                "//div[./h5[text() = 'Estado de cuenta']]",
            )

            debt_text = debt_panel.find_element(
                "xpath",
                ".//div[./p[text() = 'TOTAL A PAGAR']]/p[2] | .//span[contains(text(), 'no posee deuda')]",
            ).text

            logger.info("Debt elements found")

            debt = 0
            if debt_text != "Al día de la fecha, su cuenta no posee deuda.":
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
