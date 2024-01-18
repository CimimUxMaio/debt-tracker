import telegrambot.presenter as presenter
import os
import config
import asyncio

from from_root import from_root
from multiprocessing import Queue
from reporter import ReportRequest, ReportReply, RequestData
from trackers import Full
from typing import Any, Callable, Coroutine, cast
from telegram import Message, Update, User
from telegram.helpers import escape_markdown
from telegram.constants import ParseMode
from datetime import time
from telegram.ext import (
    Application,
    CommandHandler,
    ApplicationBuilder,
    ContextTypes,
    Job,
    JobQueue,
    ExtBot,
    PicklePersistence,
)


__all__ = ["TelegramBot"]


def build_tracker():
    return Full()


CmdHandler = Callable[
    [Any, Update, ContextTypes.DEFAULT_TYPE], Coroutine[Any, Any, None]
]


def secure_command(func: CmdHandler) -> CmdHandler:
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = cast(Message, update.message)
        if not self.is_authorized(msg.from_user):
            await msg.reply_text("Usted no esta autorizado para realizar esta acción.")
            return
        return await func(self, update, context)

    return wrapper


class TelegramBot:
    _bot: ExtBot | None = None
    _sub_jobs: dict[int, Job] = {}

    def __init__(
        self, request_queue: "Queue[ReportRequest]", reply_queue: "Queue[ReportReply]"
    ):
        self.request_queue = request_queue
        self.reply_queue = reply_queue
        self.user_white_list = (
            os.getenv("USER_WHITE_LIST", "").replace(" ", "").lower().split(",")
        )

    async def receiver_loop(self):
        while True:
            loop = asyncio.get_event_loop()
            reply = await loop.run_in_executor(None, self.reply_queue.get)
            if reply.data.purpose == "notification":
                await self.send_notification(reply)
            else:
                markdown = presenter.markdown(reply.reports)
                await self.bot.send_message(
                    reply.data.chat_id,
                    markdown,
                    parse_mode=ParseMode.MARKDOWN_V2,
                )

    def run(self, token: str, persist: bool = True):
        builder = ApplicationBuilder().token(token)
        if persist:
            data_path = from_root("data/subscriptions.pickle")
            persistence = PicklePersistence(filepath=data_path)
            builder.persistence(persistence).post_init(self.restore_subscriptions)

        app = builder.build()
        self.setup_application(app)
        loop = asyncio.get_event_loop()
        loop.create_task(self.receiver_loop())
        self._bot = app.bot
        app.run_polling()

    def setup_application(self, app: Application):
        app.add_handlers(
            [
                CommandHandler("start", self.cmdstart),
                CommandHandler("suscribir", self.cmdsubscribe),
                CommandHandler("desuscribir", self.cmdunsubscribe),
                CommandHandler("informe", self.cmdreport),
            ]
        )

    @property
    def bot(self) -> ExtBot:
        if self._bot is None:
            raise Exception("Bot is not initialized")
        return self._bot

    def create_job(self, chat_id: int, job_queue: JobQueue):
        return job_queue.run_daily(
            lambda _: self.request_report(chat_id, "notification"),
            time=time.fromisoformat(config.REPORT_TIME),
            days=(config.REPORT_DAY,),
        )

    async def restore_subscriptions(self, app: Application):
        job_queue = cast(JobQueue, app.job_queue)
        for chat_id, data in app.chat_data.items():
            if data.get("is_subscribed", False):
                self._sub_jobs[chat_id] = self.create_job(chat_id, job_queue)

    async def request_report(self, chat_id: int, purpose: str = ""):
        tracker = build_tracker()
        data = RequestData(chat_id, purpose)
        self.request_queue.put_nowait(ReportRequest(tracker, data))

    async def send_notification(self, reply: ReportReply):
        markdown = presenter.markdown(reply.reports)
        footer = escape_markdown(
            "Si no queres continuar recibiendo estas notificaciones, utiliza /desuscribir.",
            version=2,
        )
        await self.bot.send_message(
            reply.data.chat_id,
            markdown + f"\n\n\n_{footer}_",
            parse_mode=ParseMode.MARKDOWN_V2,
        )

    def is_authorized(self, user: User | None):
        return user is not None and user.name.lower() in self.user_white_list

    # Commands

    async def cmdstart(self, update: Update, _: ContextTypes.DEFAULT_TYPE):
        msg = cast(Message, update.message)
        user = cast(User, msg.from_user)

        reply = "\n".join(
            [
                f"Hola {user.full_name}!",
                "Para suscribirte a mis notificaciones utiliza el comando /suscribir.",
            ]
        )

        await msg.reply_text(reply)

    @secure_command
    async def cmdsubscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = cast(Message, update.message)
        job_queue = cast(JobQueue, context.job_queue)

        if context.chat_data is None:
            await msg.reply_text("No se puede suscribir a notificaciones.")
            return

        if context.chat_data.get("is_subscribed", False):
            reply = "Ya estás suscripto a mis notificaciones."
            await msg.reply_text(reply)
            return

        job = self.create_job(msg.chat_id, job_queue)
        self._sub_jobs[msg.chat_id] = job

        context.chat_data["is_subscribed"] = True

        reply = "\n".join(
            [
                "Te has suscripto a mis notificaciones.",
                "Recuerda que puedes desuscribirte utilizando /desuscribir.",
            ]
        )
        await msg.reply_text(reply)

    async def cmdunsubscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = cast(Message, update.message)

        if context.chat_data is None:
            await msg.reply_text("No se puede desuscribir a notificaciones.")
            return

        if not context.chat_data.get("is_subscribed", False):
            await msg.reply_text("No estas suscrito a mis notificaciones.")
            return

        del context.chat_data["is_subscribed"]

        job = self._sub_jobs.get(msg.chat_id, None)
        if job is not None:
            job.schedule_removal()
            del self._sub_jobs[msg.chat_id]

        reply = "\n".join(
            [
                "Te has desuscripto.",
                "Recuerda que puedes volver a suscribirte utilizando /suscribir.",
            ]
        )
        await msg.reply_text(reply)

    @secure_command
    async def cmdreport(self, update: Update, _: ContextTypes.DEFAULT_TYPE):
        msg = cast(Message, update.message)
        await self.request_report(msg.chat_id)
        await msg.reply_text(
            "Estoy generando el informe, esto puede tomar algunos minutos."
        )
