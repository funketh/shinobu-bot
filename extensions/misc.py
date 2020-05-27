import random

import discord
from discord.ext import commands

from api import shinobu
from api.my_context import Context


class Misc(commands.Cog):
    @commands.command()
    async def blame(self, ctx: Context, user: discord.User):
        """Blame someone."""
        await ctx.send(f'Blame {user.mention} for everything!')

    @commands.command(aliases=['coin'])
    async def flip(self, ctx: Context):
        """Flip a coin."""
        side_chance = 1/6000
        result = random.choices(["Heads!", "Tails!", "The coin landed on its side!"],
                                weights=[.5 - side_chance, .5 - side_chance, side_chance])[0]
        await ctx.send(result)


def setup(bot: shinobu.Shinobu):
    bot.add_cog(Misc())
