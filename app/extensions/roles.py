import logging
import asyncio
from typing import Optional, List

import discord
from sentry_sdk import capture_exception, Hub
from discord.ext import commands, tasks

import config
from constants import GUILD_INDEX
from app.constants import (
    MASTER_ROLE_ID,
    VALIANT_ROLE_ID,
    VALIANT_ROLE,
    MASTER_ROLE,
    APPRENTICE_ROLE,
    APPRENTICE_ROLE_ID,
    ALCHEMIST_ROLE,
)
from app.models import Notification
from app.utils import fetch_alchemists_data
from app.constants import NotificationTypes


class RolesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.lock = asyncio.Lock()
        self.guild: discord.Guild
        self.members: List[discord.Member]
        self.new_data_poll_cron_task.start()

    @tasks.loop(seconds=config.POLL_DATA_SECONDS)
    async def new_data_poll_cron_task(self):
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

    @new_data_poll_cron_task.before_loop
    async def before_new_data_poll_cron_task(self):
        await self.bot.wait_until_ready()
        self.guild = self.bot.guilds[GUILD_INDEX]

    async def do_periodic(self):
        alchemists_data = await fetch_alchemists_data()
        # refresh members
        await self.fetch_all_members()

        # loop over alchemists data and check user points
        for data_item in alchemists_data:
            username = self.clean_username(str(data_item["discord"]))
            member = await self.get_member_or_none(username)
            if member is not None:
                await self.assign_role(member=member, role_id=data_item["rank_n"])

    async def fetch_all_members(self) -> None:
        """Get fresh list of up to date members"""
        self.members = []
        async for member in self.guild.fetch_members(limit=None):
            self.members.append(member)

    def clean_username(self, username: str) -> str:
        if " #" in username:
            username = username.replace(" #", "#")
        if "# " in username:
            username = username.replace("# ", "#")
        if " @" in username:
            username = username.replace(" @", "@")
        if "@ " in username:
            username = username.replace("@ ", "@")
        # remove spaces at the beginning and at the end
        username = username.strip()
        return username

    def get_username(self, member: discord.Member) -> str:
        return f"{member.name}#{member.discriminator}"

    async def get_member_or_none(self, username: str) -> Optional[discord.Member]:
        member = [_ for _ in self.members if self.check_username_modifications(self.get_username(_), username)]
        if not member and "#" in username:
            logging.debug(f":::role_sheet: Could not find member '{username}'")
            return None
        elif not member and "#" not in username:
            members = [_ for _ in self.members if _.name == username]
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
        if discord_username == username:
            return True
        if discord_username == username.replace("@", "#"):
            return True
        if discord_username.lower() == username.lower():
            return True
        # check modified username
        if "#" in username and username.count("#") == 1:
            name, tag = username.split("#")
            return discord_username == f"{name} | Alchemist#{tag}"
        else:
            username = f"{username} | Alchemist"
            return discord_username == f"{username} | Alchemist"
        return False

    async def assign_role(self, member: discord.Member, role_id: int) -> None:
        # get roles objects
        alchemist_role = discord.utils.get(self.guild.roles, name=ALCHEMIST_ROLE)
        apprentice_role = discord.utils.get(self.guild.roles, name=APPRENTICE_ROLE)
        valiant_role = discord.utils.get(self.guild.roles, name=VALIANT_ROLE)
        master_role = discord.utils.get(self.guild.roles, name=MASTER_ROLE)
        # run checks
        member_has_apprentice_role = discord.utils.get(member.roles, name=APPRENTICE_ROLE)
        member_has_valiant_role = discord.utils.get(member.roles, name=VALIANT_ROLE)
        member_has_master_role = discord.utils.get(member.roles, name=MASTER_ROLE)
        member_should_be_promoted_to_apprentice = role_id == APPRENTICE_ROLE_ID
        member_should_be_promoted_to_valiant = role_id == VALIANT_ROLE_ID
        member_should_be_promoted_to_master = role_id == MASTER_ROLE_ID
        # assign roles
        if member_should_be_promoted_to_master:
            if not member_has_master_role:
                await self.schedule_notification(member=member, notification_type=NotificationTypes.GREET_MASTER)
                await member.add_roles(*[master_role, alchemist_role], reason="RoleSheetBot")
                # remove apprentice and valiant roles
                await member.remove_roles(*[apprentice_role, valiant_role], reason="RoleSheetBot")
        elif member_should_be_promoted_to_valiant:
            if not member_has_valiant_role:
                await self.schedule_notification(member=member, notification_type=NotificationTypes.GREET_VALIANT)
                await member.add_roles(*[valiant_role, alchemist_role], reason="RoleSheetBot")
                # remove apprentice and master roles
                await member.remove_roles(*[apprentice_role, master_role], reason="RoleSheetBot")
        elif member_should_be_promoted_to_apprentice:
            if not member_has_apprentice_role:
                await self.schedule_notification(member=member, notification_type=NotificationTypes.GREET_APPRENTICE)
                await member.add_roles(*[apprentice_role, alchemist_role], reason="RoleSheetBot")
                # remove valiant and master roles
                await member.remove_roles(*[valiant_role, master_role], reason="RoleSheetBot")
        return None

    async def log(self, msg: str) -> None:
        channel = self.guild.get_channel(config.LOG_CHANNEL_ID)
        # prevent duplicate logs
        if not await self.exists_message_in_channel(msg, channel):
            await channel.send(msg)

    async def schedule_notification(self, member: discord.Member, notification_type: NotificationTypes) -> None:
        channel = self.guild.get_channel(config.WELCOME_CHANNEL_ID)
        notification_text = ""
        if notification_type == NotificationTypes.GREET_MASTER:
            notification_text = f"Greatness is achieved with hard work and you {member.mention} have earned your role as **Master Alchemist**. The same vision that brought you here will inspire others and together you'll build a legacy!"  # noqa: E501
        elif notification_type == NotificationTypes.GREET_VALIANT:
            notification_text = f"The path you've paved so far has opened up a new chapter for you {member.mention}. Embrace your new role as **Valiant Alchemist** and enjoy this new venture!"  # noqa: E501
        elif notification_type == NotificationTypes.GREET_APPRENTICE:
            notification_text = f"Only a few possess the skills of a true **Apprentice Alchemist** and you {member.mention} are one of them! Good luck on this new journey!"  # noqa: E501
        # prevent duplicate notifications
        await Notification.get_or_create(
            user_id=member.id,
            notification_type=notification_type,
            channel_id=channel.id,
            defaults={
                "text": notification_text,
                "is_sent": not config.DO_SEND_NOTIFICATIONS,  # we will handle sending in separate cron task
            },
        )

    async def exists_message_in_channel(self, msg: str, channel: discord.abc.GuildChannel) -> bool:
        """Searches for exact message, if it exists returns True"""
        messages = await channel.history(limit=None, oldest_first=True).flatten()
        for message in messages:
            if message.content == msg and message.author == self.bot.user:
                return True
        return False


def setup(bot):
    bot.add_cog(RolesCog(bot))
