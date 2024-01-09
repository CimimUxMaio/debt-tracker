from typing import cast
from telegram import Message, Update, User
from telegram.ext import (
    Application,
    CommandHandler,
    ApplicationBuilder,
    ContextTypes,
    Job,
    JobQueue,
)


__all__ = ["run"]


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
        ]
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

    async def send_notification(ctx: ContextTypes.DEFAULT_TYPE):
        await ctx.bot.send_message(msg.chat_id, "Notificacion")

    if context.user_data is None:
        await msg.reply_text("No se puede suscribir a notificaciones.")
        return

    if context.user_data.get("job"):
        reply = "\n".join(
            [
                "Ya estás suscripto a mis notificaciones.",
                "Utiliza /configurar para reconfigurar tus notificaciones.",
            ]
        )
        await msg.reply_text(reply)
        return

    job = job_queue.run_repeating(send_notification, 10)
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
