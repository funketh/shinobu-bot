import discord
from discord.ext import commands

from CONSTANTS import CURRENCY
from shinobu import Shinobu
from utils import database

class Economy(commands.Cog):
    @commands.command(name='balance', aliases=['bl'])
    async def balance_cmd(self, ctx: commands.Context, user: discord.User = None):
        """Get a user's balance"""
        user = user or ctx.author
        db = database.connect()
        balance = db.execute('SELECT balance FROM user WHERE id=?', [user.id]).fetchone()['balance']
        await ctx.send(embed=discord.Embed(color=discord.Colour.green(),
                                           description=f'{user.mention}\'s balance: {balance}{CURRENCY}'))

    async def on_message(self, message: discord.Message): pass

def setup(bot: Shinobu):
    bot.add_cog(Economy(bot))
