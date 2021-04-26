from discord import Activity, ActivityType
from discord.ext import commands


class CommonCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.change_presence(activity=Activity(type=ActivityType.watching, name="Google Sheets"))
        info = await self.bot.application_info()
        print(f"Add via link: https://discord.com/oauth2/authorize?client_id={info.id}&scope=bot&permissions=8")


def setup(bot):
    bot.add_cog(CommonCog(bot))
