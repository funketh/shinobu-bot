import discord
from discord.ext import commands

from api import shinobu
from api.my_context import Context


class Misc(commands.Cog):
    @commands.command()
    async def blame(self, ctx: Context, user: discord.User):
        """Blame someone"""
        await ctx.send(f'Blame {user.mention} for everything!')


def setup(bot: shinobu.Shinobu):
    bot.add_cog(Misc())
