import logging
from collections import Counter
from datetime import datetime, timedelta
from typing import Optional, List, Tuple

import discord
from discord.ext import commands, tasks

from api.my_context import Context
from api.shinobu import Shinobu
from data.CONSTANTS import CURRENCY
from utils import database
from utils import mal_rss
from utils.database import User

logger = logging.getLogger(__name__)


class Economy(commands.Cog):
    def __init__(self, bot: Shinobu):
        self.bot = bot
        self.birthday.start()
        self.reward_media_consumption.start()

    async def on_ready(self):
        await self.birthday.coro()

    @tasks.loop(hours=24)
    async def birthday(self):
        with database.connect() as db:
            for user_row in db.execute("SELECT * FROM user WHERE birthday == DATE('now', 'localtime')").fetchall():
                db.execute('UPDATE user SET balance=balance+100, birthday=? WHERE id=?',
                           [add_years(user_row['birthday'], 1), user_row['id']])
                user: discord.User = self.bot.get_user(user_row['id'])
                await user.send(f'🎉🎉🎉 Happy Birthday! 🎉🎉🎉\nAs a present, you get 100 {CURRENCY}!')
                logger.info(f'gifted 100 to {user.name} as a birthday present!')

    @commands.command(aliases=['b'])
    async def balance(self, ctx: Context, user: Optional[discord.User] = None):
        """Get a user's balance"""
        user = user or ctx.author
        with database.connect() as db:
            user_data = User.build(**db.execute('SELECT * FROM user WHERE id=?', [user.id]).fetchone())
            income, new_last_withdrawal = income_and_new_last_withdrawal(user_data)
            if income:
                if user == ctx.author:
                    db.execute('UPDATE user SET balance=balance+?, last_withdrawal=? WHERE id=?',
                               [income, new_last_withdrawal, user.id])
                    income_msg = f'  (Withdrew {income} {CURRENCY})'
                    logger.info(f'{ctx.author.name} withdrew {income} from their passive income')
                else:
                    income_msg = f'  (Has yet to withdraw {income} {CURRENCY})'
            else:
                income_msg = ''
        await ctx.info(f'{user.mention}\'s balance: {user_data.balance + income} {CURRENCY}{income_msg}')

    @tasks.loop(hours=1)
    async def reward_media_consumption(self):
        logger.debug('rewarding media consumption...')
        db = database.connect()
        users = db.execute("SELECT id, mal_username FROM user WHERE mal_username > ''").fetchall()
        new_entries: List[Tuple[int, str, int, int]] = []
        rewarded_money: Counter[int, int] = Counter()
        for u in users:
            for content_type in ('anime',):
                new_content = mal_rss.new_mal_content(db, content_type, u['id'], u['mal_username'])
                for series_id, old_amount, consumed_amount in new_content:
                    logger.info(f'user {u["id"]} consumed {consumed_amount - old_amount}'
                                f' bits of {series_id} ({content_type})')
                    new_entries.append((u['id'], content_type, series_id, consumed_amount))
                    rewarded_money[u['id']] += await mal_rss.calculate_reward(
                        content_type, series_id, consumed_amount - old_amount
                    )
        with db:
            db.executemany('REPLACE INTO consumed_media(user,type,id,amount) VALUES(?,?,?,?)', new_entries)
            db.executemany('UPDATE user SET balance=balance+? WHERE id=?',
                           [(amount, id_) for id_, amount in rewarded_money.items()])

    @commands.cooldown(1, 60)
    @commands.command(aliases=['up'])
    async def update(self, ctx: Context):
        """Force a full update of everyone's earnings"""
        await self.reward_media_consumption.coro(self)
        await ctx.info("Success!")


def add_years(date_: str, amount: int) -> str:
    return str(int(date_[:4]) + amount) + date_[4:]


def income_and_new_last_withdrawal(user: User) -> Tuple[int, datetime]:
    income_in_seconds = (3600 * 5)
    last_withdrawal = datetime.fromisoformat(user.last_withdrawal)
    full_delta = datetime.today() - last_withdrawal
    full_income = int(full_delta.total_seconds() // income_in_seconds)
    rewarded_delta = timedelta(seconds=full_income * income_in_seconds)
    new_last_withdrawal = last_withdrawal + rewarded_delta
    income = min(full_income, 10)
    return income, new_last_withdrawal


def setup(bot: Shinobu):
    bot.add_cog(Economy(bot))
