import discord
import logging
from discord.ext import commands, tasks
from typing import Optional

from api.my_context import Context
from data.CONSTANTS import CURRENCY
from api.shinobu import Shinobu
from utils import database

logger = logging.getLogger(__name__)


class Economy(commands.Cog):
    def __init__(self, bot: Shinobu):
        self.bot = bot
        self.passive_income.start()
        self.birthday.start()

    async def on_ready(self):
        await self.birthday.coro()

    def cog_unload(self):
        self.passive_income.cancel()

    @tasks.loop(hours=3)
    async def passive_income(self):
        db = database.connect()
        with db:
            db.execute('UPDATE user SET income=MIN(income+1, 25)')

    @tasks.loop(hours=24)
    async def birthday(self):
        db = database.connect()
        with db:
            for user_row in db.execute("SELECT * FROM user WHERE birthday == DATE('now', 'localtime')").fetchall():
                db.execute('UPDATE user SET balance=balance+100, birthday=? WHERE id=?',
                           [add_years(user_row['birthday'], 1), user_row['id']])
                user: discord.User = self.bot.get_user(user_row['id'])
                await user.send(f'🎉🎉🎉 Happy Birthday! 🎉🎉🎉\nAs a present, you get 100 {CURRENCY}!')
                logger.info(f'gifted 100 to {user.name} as a birthday present!')

    @commands.command(aliases=['p'])
    async def passive_income(self, ctx: Context):
        """Withdraw accumulated passive income"""
        db = database.connect()
        with db:
            amount = db.execute('SELECT income FROM user WHERE id=?', [ctx.author.id]).fetchone()[0]
            db.execute('UPDATE user SET balance=balance+?, income=0 WHERE id=?', [amount, ctx.author.id])
        await ctx.info(f'Withdrew {amount} {CURRENCY}')

    @commands.command(aliases=['b'])
    async def balance(self, ctx: Context, user: Optional[discord.User] = None):
        """Get a user's balance"""
        user = user or ctx.author
        db = database.connect()
        balance = db.execute('SELECT balance FROM user WHERE id=?', [user.id]).fetchone()['balance']
        await ctx.info(f'{user.mention}\'s balance: {balance} {CURRENCY}')


def add_years(date_: str, amount: int) -> str:
    return str(int(date_[:4]) + amount) + date_[4:]


def setup(bot: Shinobu):
    bot.add_cog(Economy(bot))
