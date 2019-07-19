import discord
from discord.ext import commands

from api import shinobu
from api.my_context import Context


class Blame(commands.Cog):
    @commands.command(name='blame')
    async def blame_cmd(self, ctx: Context, user: discord.User):
        await ctx.send(f'Blame {user.mention} for everything!')


def setup(bot: shinobu.Shinobu):
    bot.add_cog(Blame())
