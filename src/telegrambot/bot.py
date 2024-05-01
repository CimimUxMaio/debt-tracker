import telegrambot.presenter as presenter
import config
import asyncio
import telegrambot.utils as utils
import logging
import pytz

from from_root import from_root
from multiprocessing import Queue
from reporter import ReportRequest, ReportReply
from telegrambot.types import CommandInfo
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
    ExtBot,
    PicklePersistence,
)


__all__ = ["TelegramBot"]


logger = logging.getLogger(__name__)


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
    _app: Application | None = None

    def __init__(
        self, request_queue: "Queue[ReportRequest]", reply_queue: "Queue[ReportReply]"
    ):
        self.request_queue = request_queue
        self.reply_queue = reply_queue
        self.user_white_list = (
            config.USER_WHITE_LIST.replace(" ", "").lower().split(",")
        )

    def run(self, token: str, persist: bool = True):
        app = self.build_application(token, persist)
        self._app = app  # Set app instance for easy access

        # Run report receiver
        loop = asyncio.get_event_loop()
        receiver = ReportReceiver(app.bot, self.reply_queue)
        loop.create_task(receiver.run())

        self.create_scheduled_report_job(app)

        app.run_polling()

    def build_application(self, token: str, persist: bool = True) -> Application:
        builder = ApplicationBuilder().token(token)
        if persist:
            data_path = from_root("data/subscriptions.pickle")
            persistence = PicklePersistence(filepath=data_path)
            builder.persistence(persistence)

        app = builder.post_init(self.post_init).build()
        return app

    @property
    def app(self) -> Application:
        if self._app is None:
            raise Exception("App is not initialized")
        return self._app

    @property
    def bot(self) -> ExtBot:
        return self.app.bot

    @property
    def subscriptions(self) -> list[int]:
        return [
            chat_id
            for chat_id, data in self.app.chat_data.items()
            if data.get("is_subscribed", False)
        ]

    @property
    def commands_info(self) -> list[CommandInfo]:
        return [
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

    def create_scheduled_report_job(self, app: Application):
        job_queue = app.job_queue
        if job_queue is None:
            raise Exception("JobQueue is not initialized")

        async def notify_subscribers(_):
            logger.info("Running scheduled report job")
            return await self.request_report(self.subscriptions, "scheduled")

        timezone = pytz.timezone("America/Argentina/Buenos_Aires")
        report_time = time.fromisoformat(config.REPORT_TIME).replace(tzinfo=timezone)
        logger.info(
            f"Notifications scheduled for day {config.REPORT_DAY} at {report_time}"
        )
        return job_queue.run_daily(
            notify_subscribers,
            time=report_time,
            days=(config.REPORT_DAY,),
        )

    async def set_commands(self, app: Application):
        await app.bot.set_my_commands(
            [
                (info.name, info.description)
                for info in self.commands_info
                if not info.private
            ]
        )

    async def post_init(self, app: Application):
        await self.set_commands(app)
        app.add_handlers(
            [CommandHandler(info.name, info.handler) for info in self.commands_info]
        )

    async def request_report(self, chat_ids: list[int], purpose: str = ""):
        self.request_queue.put_nowait(ReportRequest(chat_ids, purpose))

    def is_authorized(self, user: User | None):
        return user is not None and user.name.lower() in self.user_white_list

    def is_subscribed(self, chat_id: int):
        return chat_id in self.subscriptions

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

        if context.chat_data is None:
            await msg.reply_text("No se puede suscribir a notificaciones.")
            return

        if self.is_subscribed(msg.chat_id):
            reply = "Ya estás suscripto a mis notificaciones."
            await msg.reply_text(reply)
            return

        # Add subscription flag to chat_data
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

        if not self.is_subscribed(msg.chat_id):
            await msg.reply_text("No estas suscrito a mis notificaciones.")
            return

        # Remove subscription flag from chat_data
        del context.chat_data["is_subscribed"]

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
        await self.request_report([msg.chat_id])

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


class ReportReceiver:
    def __init__(self, bot: ExtBot, reply_queue: "Queue[ReportReply]"):
        self.bot = bot
        self.reply_queue = reply_queue

    async def run(self):
        while True:
            loop = asyncio.get_event_loop()
            reply = await loop.run_in_executor(None, self.reply_queue.get)
            await self.send_reply(reply)

    async def send_reply(self, reply: ReportReply):
        markdown = presenter.markdown(reply.reports)

        # If the request is a scheduled notification, add a footer with the unsubscribe message
        footer = ""
        if reply.request.purpose == "scheduled":
            footer = escape_markdown(
                "Si no queres continuar recibiendo estas notificaciones, utiliza /desuscribir.",
                version=2,
            )
            footer = f"\n\n\n_{footer}_"

        # Send the report to all chat_ids
        for chat_id in reply.request.chat_ids:
            await self.bot.send_message(
                chat_id,
                markdown + footer,
                parse_mode=ParseMode.MARKDOWN_V2,
            )
