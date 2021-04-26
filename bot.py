import sys
import logging

from discord import Intents
from tortoise import Tortoise
from discord.ext import commands

import config
from constants import SENTRY_ENV_NAME, TORTOISE_ORM
from app.utils import use_sentry


# initialize bot params
intents = Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!role.", help_command=None, intents=intents)


# init sentry SDK
use_sentry(
    bot,
    dsn=config.SENTRY_API_KEY,
    environment=SENTRY_ENV_NAME,
    integrations=[],
)

# setup logger
file_handler = logging.FileHandler(filename="covalent-role-sheet.log")
stdout_handler = logging.StreamHandler(sys.stdout)

logging.basicConfig(
    level=logging.getLevelName(config.LOG_LEVEL),
    format="%(asctime)s %(levelname)s:%(message)s",
    handlers=[file_handler if config.LOG_TO_FILE else stdout_handler],
)


if __name__ == "__main__":
    bot.load_extension("app.extensions.common")
    bot.load_extension("app.extensions.main")
    bot.loop.run_until_complete(Tortoise.init(config=TORTOISE_ORM))
    bot.run(config.TOKEN)
