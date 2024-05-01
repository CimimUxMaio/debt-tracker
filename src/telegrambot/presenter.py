from telegram.helpers import escape_markdown
from scrappers.types import ScrapperReport, DebtReport


def debt_report_markdown(report: DebtReport) -> str:
    formatted_debt = f"{report.debt:_.2f}".replace(".", ",").replace("_", ".")
    return "\n".join(
        [
            f"\\- {escape_markdown(report.address, version=2)}",
            f"  Deuda: _${escape_markdown(formatted_debt, version=2)}_",
        ]
    )


def scrapper_report_markdown(report: ScrapperReport) -> str:
    report_title = f"*[{escape_markdown(report.title, version=2)}]({escape_markdown(report.link)})*"

    if report.content is None:
        report_body = "Ocurrio un error al generar el informe\\."
    else:
        report_body = "\n\n".join(
            [debt_report_markdown(report) for report in report.content]
        )

    return report_title + "\n" + report_body


def markdown(reports: list[ScrapperReport]):
    title = "__*Informe de Deudas\\:*__"
    report_body = "\n\n".join([scrapper_report_markdown(report) for report in reports])
    markdown = title + "\n\n" + report_body
    return markdown
