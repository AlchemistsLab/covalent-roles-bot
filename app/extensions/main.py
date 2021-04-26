import logging
import asyncio
from typing import Optional

import discord
from discord.ext import commands, tasks

import config
from constants import GUILD_INDEX
from app.utils import SheetsHelper
from app.constants import (
    VALIANT_ROLE_POINTS_THRESHOLD,
    MASTER_ROLE_POINTS_THRESHOLD,
    VALIANT_ROLE,
    MASTER_ROLE,
    APPRENTICE_ROLE,
    APPRENTICE_ROLE_POINTS_THRESHOLD,
    USERNAME_COLUMN,
    POINTS_COLUMN,
)
from app.models import Notification
from app.constants import NotificationTypes


class MainCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.lock = asyncio.Lock()
        self.guild: discord.Guild
        self.sheet = SheetsHelper()
        self.google_sheets_poll_cron_task.start()

    @tasks.loop(seconds=config.POLL_GOOGLE_SHEETS_SECONDS)
    async def google_sheets_poll_cron_task(self):
        # ensure that only one instance of job is running, other instances will be discarded
        if not self.lock.locked():
            await self.lock.acquire()
            try:
                await self.do_periodic()
            finally:
                self.lock.release()

    @google_sheets_poll_cron_task.before_loop
    async def before_google_sheets_poll_cron_task(self):
        await self.bot.wait_until_ready()
        self.guild = self.bot.guilds[GUILD_INDEX]

    async def do_periodic(self):
        await self.sheet.init()
        google_sheets_data = await self.sheet.get_data()

        # parse users and points data
        tab_name = next(iter(google_sheets_data))
        tab_data = google_sheets_data[tab_name]

        # loop over tab data and check user points
        for data_item in tab_data:
            username = self.clean_username(data_item[USERNAME_COLUMN])
            points = data_item[POINTS_COLUMN]
            member = await self.get_member_or_none(username)
            if member is not None and isinstance(points, int):
                await self.assign_roles_based_on_points(member=member, points=points)

    def clean_username(self, username: str) -> str:
        if " #" in username:
            username = username.replace(" #", "#")
        if "# " in username:
            username = username.replace("# ", "#")
        if " @" in username:
            username = username.replace(" @", "@")
        if "@ " in username:
            username = username.replace("@ ", "@")
        return username

    async def get_member_or_none(self, username: str) -> Optional[discord.Member]:
        member = [
            _ for _ in self.guild.members if str(_) == username or self.check_username_modifications(str(_), username)
        ]
        if not member and "#" in username:
            logging.debug(f":::role_sheet: Could not find member '{username}'")
            return None
        elif not member and "#" not in username:
            members = [_ for _ in self.guild.members if _.name == username]
            if not members:
                logging.debug(f":::role_sheet: Could not find member '{username}'")
                return None
            elif len(members) > 1:
                logging.debug(f":::role_sheet: More than one user goes by the name of: '{username}'")
                await self.log(f"More than one user goes by the name of: `{username}`")
                return None
            member = members[0]
        else:
            member = member[0]
        return member

    def check_username_modifications(self, discord_username: str, username: str) -> bool:
        if discord_username == username.replace("@", "#"):
            return True
        # check modified username
        if "#" in username:
            name, tag = username.split("#")
            return discord_username == f"{name} | Alchemist#{tag}"
        else:
            username = f"{username} | Alchemist"
            return discord_username == f"{username} | Alchemist"
        return False

    async def assign_roles_based_on_points(self, member: discord.Member, points: int) -> None:
        # get roles objects
        apprentice_role = discord.utils.get(self.guild.roles, name=APPRENTICE_ROLE)
        valiant_role = discord.utils.get(self.guild.roles, name=VALIANT_ROLE)
        master_role = discord.utils.get(self.guild.roles, name=MASTER_ROLE)
        # run checks
        member_has_apprentice_role = discord.utils.get(member.roles, name=APPRENTICE_ROLE)
        member_has_valiant_role = discord.utils.get(member.roles, name=VALIANT_ROLE)
        member_has_master_role = discord.utils.get(member.roles, name=MASTER_ROLE)
        member_should_be_promoted_to_apprentice = points >= APPRENTICE_ROLE_POINTS_THRESHOLD
        member_should_be_promoted_to_valiant = points >= VALIANT_ROLE_POINTS_THRESHOLD
        member_should_be_promoted_to_master = points >= MASTER_ROLE_POINTS_THRESHOLD
        # assign roles
        if member_should_be_promoted_to_master:
            if not member_has_master_role:
                await member.add_roles(master_role, reason="GSheet")
                # remove apprentice and valiant roles
                await member.remove_roles(*[apprentice_role, valiant_role], reason="Master role")
                await self.notify(member=member, notification_type=NotificationTypes.GREET_MASTER)
        elif member_should_be_promoted_to_valiant:
            if not member_has_valiant_role:
                await member.add_roles(valiant_role, reason="GSheet")
                # remove apprentice and master roles
                await member.remove_roles(*[apprentice_role, master_role], reason="Valiant role")
                await self.notify(member=member, notification_type=NotificationTypes.GREET_VALIANT)
        elif member_should_be_promoted_to_apprentice:
            if not member_has_apprentice_role:
                await member.add_roles(apprentice_role, reason="GSheet")
                # remove valiant and master roles
                await member.remove_roles(*[valiant_role, master_role], reason="Apprentice role")
                await self.notify(member=member, notification_type=NotificationTypes.GREET_APPRENTICE)
        return None

    async def log(self, msg: str) -> None:
        channel = self.guild.get_channel(config.LOG_CHANNEL_ID)
        # prevent duplicate logs
        if not await self.exists_message_in_channel(msg, channel):
            await channel.send(msg)

    async def notify(self, member: discord.Member, notification_type: NotificationTypes) -> None:
        channel = self.guild.get_channel(config.WELCOME_CHANNEL_ID)
        notification_text = ""
        if notification_type == NotificationTypes.GREET_MASTER:
            notification_text = f"Greetings, {member.mention} was promoted to Master Alchemist"
        elif notification_type == NotificationTypes.GREET_VALIANT:
            notification_text = f"Greetings, {member.mention} was promoted to Valiant Alchemist"
        elif notification_type == NotificationTypes.GREET_APPRENTICE:
            notification_text = f"Greetings, {member.mention} was promoted to Apprentice Alchemist"
        # prevent duplicate notifications
        _, created = await Notification.get_or_create(
            user_id=member.id,
            notification_type=notification_type,
            channel_id=channel.id,
            defaults={"text": notification_text},
        )
        if created and config.DO_SEND_NOTIFICATIONS:
            await channel.send(notification_text)

    async def exists_message_in_channel(self, msg: str, channel: discord.abc.GuildChannel) -> bool:
        """Searches for exact message, if it exists returns True"""
        messages = await channel.history(limit=None, oldest_first=True).flatten()
        for message in messages:
            if message.content == msg and message.author == self.bot.user:
                return True
        return False


def setup(bot):
    bot.add_cog(MainCog(bot))