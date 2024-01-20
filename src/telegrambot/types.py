from typing import Callable, Coroutine, NamedTuple, Any
from telegram import Update
from telegram.ext import ContextTypes


class CommandInfo(NamedTuple):
    name: str
    handler: Callable[[Update, ContextTypes.DEFAULT_TYPE], Coroutine[Any, Any, None]]
    description: str = ""
    help: str = ""
    private: bool = False
