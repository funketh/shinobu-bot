import discord
from discord.ext import commands

import shinobu


class Blame(commands.Cog):
    @commands.command(name='blame')
    async def blame_cmd(self, ctx: commands.Context, user: discord.User):
        await ctx.send(f'Blame {user.mention} for everything!')


def setup(bot: shinobu.Shinobu):
    bot.add_cog(Blame())
