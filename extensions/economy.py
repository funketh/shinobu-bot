import discord
from discord.ext import commands, tasks

from CONSTANTS import CURRENCY
from shinobu import Shinobu
from utils import database
from utils.messages import inform


class Economy(commands.Cog):
    def __init__(self, bot: Shinobu):
        self.bot = bot
        self.passive_income.start()

    def cog_unload(self):
        self.passive_income.cancel()

    @tasks.loop(hours=3)
    async def passive_income(self):
        db = database.connect()
        with db:
            db.execute('UPDATE user SET income=MIN(income+1, 25)')

    @commands.command(name='withdraw', aliases=['w'])
    async def withdraw_income_cmd(self, ctx: commands.Context):
        """Withdraw accumulated passive income"""
        db = database.connect()
        with db:
            amount = db.execute('SELECT income FROM user WHERE id=?', [ctx.author.id]).fetchone()[0]
            db.execute('UPDATE user SET balance=balance+?, income=0 WHERE id=?', [amount, ctx.author.id])
        await inform(ctx, f'Withdrew {amount}{CURRENCY}')

    @commands.command(name='balance', aliases=['bl'])
    async def balance_cmd(self, ctx: commands.Context, user: discord.User = None):
        """Get a user's balance"""
        user = user or ctx.author
        db = database.connect()
        balance = db.execute('SELECT balance FROM user WHERE id=?', [user.id]).fetchone()['balance']
        await inform(ctx, f'{user.mention}\'s balance: {balance}{CURRENCY}')


def setup(bot: Shinobu):
    bot.add_cog(Economy(bot))
