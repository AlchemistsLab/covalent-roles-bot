import logging
import asyncio

import discord
from sentry_sdk import capture_exception, Hub
from discord.ext import commands, tasks

import config
from constants import GUILD_INDEX
from app.constants import WELCOME_REACTION
from app.models import Notification


class NotificationsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.lock = asyncio.Lock()
        self.guild: discord.Guild
        self.notifications_cron_task.start()

    @tasks.loop(seconds=120)
    async def notifications_cron_task(self):
        # ensure that only one instance of job is running, other instances will be discarded
        with Hub(Hub.current):
            if not self.lock.locked():
                await self.lock.acquire()
                try:
                    await self.do_periodic()
                except Exception as e:
                    logging.debug(f":::role_sheet: {e}")
                    capture_exception(e)
                finally:
                    self.lock.release()

    @notifications_cron_task.before_loop
    async def before_notifications_cron_task(self):
        await self.bot.wait_until_ready()
        self.guild = self.bot.guilds[GUILD_INDEX]

    async def do_periodic(self):
        notifications_to_send = await Notification.filter(is_sent=False)
        for notification in notifications_to_send:
            channel = self.guild.get_channel(notification.channel_id)
            message = await channel.send(notification.text)
            notification.is_sent = True
            await notification.save(update_fields=["is_sent", "modified_at"])
            # add reaction to message
            await message.add_reaction(WELCOME_REACTION)
            await asyncio.sleep(config.TIMEOUT_BETWEEN_NOTIFICATIONS)


def setup(bot):
    bot.add_cog(NotificationsCog(bot))
