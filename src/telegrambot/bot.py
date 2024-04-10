import telegrambot.presenter as presenter
import config
import asyncio
import telegrambot.utils as utils
import logging

from from_root import from_root
from multiprocessing import Queue
from reporter import ReportRequest, ReportReply, RequestData
from telegrambot.types import CommandInfo
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


logger = logging.getLogger("bot")


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
    _commands_info: list[CommandInfo] | None = None

    def __init__(
        self, request_queue: "Queue[ReportRequest]", reply_queue: "Queue[ReportReply]"
    ):
        self.request_queue = request_queue
        self.reply_queue = reply_queue
        self.tracker = Full()
        self.user_white_list = (
            config.USER_WHITE_LIST.replace(" ", "").lower().split(",")
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
            builder.persistence(persistence).post_init(self.post_init)

        app = builder.build()
        self.setup_application(app)
        loop = asyncio.get_event_loop()
        loop.create_task(self.receiver_loop())
        self._bot = app.bot
        app.run_polling()

    def setup_application(self, app: Application):
        app.add_handlers(
            [CommandHandler(info.name, info.handler) for info in self.commands_info]
        )

    @property
    def bot(self) -> ExtBot:
        if self._bot is None:
            raise Exception("Bot is not initialized")
        return self._bot

    @property
    def commands_info(self) -> list[CommandInfo]:
        if self._commands_info is None:
            self._commands_info = [
                CommandInfo(
                    name="start",
                    handler=self.cmdstart,
                    private=True,
                ),
                CommandInfo(
                    name="suscribir",
                    description="Suscribirse a las notificaciones.",
                    help=f"Utiliza este comando para suscribirte a las notificaciones recurrentes de los dias *{utils.num_to_day(config.REPORT_DAY)}* a las *{escape_markdown(config.REPORT_TIME)}* horas\\.",
                    handler=self.cmdsubscribe,
                ),
                CommandInfo(
                    name="desuscribir",
                    description="Desuscribirse de las notificaciones.",
                    help="Utiliza este comando para desuscribirte de las notificaciones recurrentes\\.",
                    handler=self.cmdunsubscribe,
                ),
                CommandInfo(
                    name="informe",
                    description="Generar informe ahora.",
                    help="Utiliza este comando para generar un informe de forma manual\\, sin necesidad de esperar a la proxima notificacion\\. La generacion del informe puede demorar unos minutos\\.",
                    handler=self.cmdreport,
                ),
                CommandInfo(
                    name="ayuda",
                    description="Mostrar mensaje de ayuda.",
                    help="Muestra este mensaje\\.",
                    handler=self.cmdhelp,
                ),
            ]

        return self._commands_info

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

    async def set_commands(self, app: Application):
        await app.bot.set_my_commands(
            [
                (info.name, info.description)
                for info in self.commands_info
                if not info.private
            ]
        )

    async def post_init(self, app: Application):
        await self.restore_subscriptions(app)
        await self.set_commands(app)

    async def request_report(self, chat_id: int, purpose: str = ""):
        data = RequestData(chat_id, purpose)
        self.request_queue.put_nowait(ReportRequest(self.tracker, data))

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
        logger.info("Command: cmdstart")
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
        logger.info("Command: cmdsubscribe")
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
        logger.info("Command: cmdunsubscribe")

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
                "Te has desuscripto de mis notificaciones.",
                "Recuerda que puedes volver a suscribirte utilizando /suscribir.",
            ]
        )
        await msg.reply_text(reply)

    @secure_command
    async def cmdreport(self, update: Update, _: ContextTypes.DEFAULT_TYPE):
        msg = cast(Message, update.message)
        logger.info("Command: cmdreport")
        await msg.reply_text(
            "Estoy generando el informe, esto puede tomar algunos minutos."
        )
        await self.request_report(msg.chat_id)

    async def cmdhelp(self, update: Update, _: ContextTypes.DEFAULT_TYPE):
        msg = cast(Message, update.message)
        logger.info("Command: cmdhelp")
        commands_help = [
            f"_*/{info.name}*_ \\- {info.help}"
            for info in self.commands_info
            if not info.private
        ]
        reply = "\n\n".join(commands_help)
        await msg.reply_text(reply, parse_mode=ParseMode.MARKDOWN_V2)
