import telegrambot.presenter as presenter
import asyncio

from trackers import Dummy, ScrapperReport, Full
from typing import cast
from telegram import Message, Update, User
from telegram.helpers import escape_markdown
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ApplicationBuilder,
    ContextTypes,
    Job,
    JobQueue,
)


__all__ = ["run"]


def build_tracker():
    return Dummy()


def run(token: str):
    app = ApplicationBuilder().token(token).build()
    setup_application(app)
    app.run_polling()


def setup_application(app: Application):
    app.add_handlers(
        [
            CommandHandler("start", start),
            CommandHandler("suscribir", subscribe),
            CommandHandler("desuscribir", unsubscribe),
            CommandHandler("informe", report),
        ]
    )


async def generate_report() -> list[ScrapperReport]:
    tracker = build_tracker()
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, tracker.run)


async def send_notification(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    reports = await generate_report()
    markdown = presenter.markdown(reports)
    footer = escape_markdown(
        "Si no queres continuar recibiendo estas notificaciones, utiliza /desuscribir.",
        version=2,
    )
    await context.bot.send_message(
        chat_id,
        markdown + f"\n\n\n_{footer}_",
        parse_mode=ParseMode.MARKDOWN_V2,
    )


# Commands


async def start(update: Update, _: ContextTypes.DEFAULT_TYPE):
    msg = cast(Message, update.message)
    user = cast(User, msg.from_user)

    reply = "\n".join(
        [
            f"Hola {user.full_name}!",
            "Para suscribirte a mis notificaciones utiliza el comando /suscribir.",
        ]
    )

    await msg.reply_text(reply)


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = cast(Message, update.message)
    job_queue = cast(JobQueue, context.job_queue)

    if context.user_data is None:
        await msg.reply_text("No se puede suscribir a notificaciones.")
        return

    if context.user_data.get("job"):
        reply = "Ya estás suscripto a mis notificaciones."
        await msg.reply_text(reply)
        return

    # job = job_queue.run_daily(
    #     lambda ctx: send_notification(msg.chat_id, ctx),
    #     time=time.fromisoformat("10:00"),
    #     days=(1,),
    # )
    job = job_queue.run_repeating(lambda ctx: send_notification(msg.chat_id, ctx), 20)

    context.user_data["job"] = job

    reply = "\n".join(
        [
            "Te has suscripto a mis notificaciones.",
            "Recuerda que puedes desuscribirte utilizando /desuscribir.",
        ]
    )
    await msg.reply_text(reply)


async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = cast(Message, update.message)

    if context.user_data is None:
        await msg.reply_text("No se puede desuscribir a notificaciones.")
        return

    job: Job | None = context.user_data.get("job")
    if not job:
        await msg.reply_text("No estas suscrito a mis notificaciones.")
        return

    job.schedule_removal()

    reply = "\n".join(
        [
            "Te has desuscripto.",
            "Recuerda que puedes volver a suscribirte utilizando /suscribir.",
        ]
    )
    await msg.reply_text(reply)


async def report(update: Update, _: ContextTypes.DEFAULT_TYPE):
    msg = cast(Message, update.message)
    reports = await generate_report()
    markdown = presenter.markdown(reports)
    await msg.reply_text(markdown, parse_mode=ParseMode.MARKDOWN_V2)
