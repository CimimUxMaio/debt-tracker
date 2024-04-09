import os
from dotenv import load_dotenv


load_dotenv()


def check_env(name: str) -> str:
    value = os.getenv(name)
    if value is None:
        raise ValueError(f"{name} environment variable is not set")
    return value


TELEGRAM_TOKEN = check_env("TELEGRAM_TOKEN")

EDENOR_EMAIL = check_env("EDENOR_EMAIL")

EDENOR_PWD = check_env("EDENOR_PWD")

EDESUR_EMAIL = check_env("EDESUR_EMAIL")

EDESUR_PWD = check_env("EDESUR_PWD")

METROGAS_EMAIL = check_env("METROGAS_EMAIL")

METROGAS_PWD = check_env("METROGAS_PWD")

USER_WHITE_LIST = check_env("USER_WHITE_LIST")

IMPLICIT_WAIT = int(check_env("IMPLICIT_WAIT"))

SCRAPPER_POOL_SIZE = int(check_env("SCRAPPER_POOL_SIZE"))

REPORT_TIME = check_env("REPORT_TIME")

REPORT_DAY = int(check_env("REPORT_DAY"))


# Optional

GECKODRIVER_PATH = os.getenv("GECKODRIVER_PATH")

FIREFOX_PATH = os.getenv("FIREFOX_PATH")
