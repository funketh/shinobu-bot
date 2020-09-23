import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple, AsyncIterator

import aiohttp
import discord
from discord.ext import commands, tasks

from api.my_context import Context
from api.shinobu import Shinobu
from data.CONSTANTS import CURRENCY, ANNOUNCEMENT_CHANNEL_ID
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

    @tasks.loop(hours=12)
    async def birthday(self):
        db = database.connect()
        for user_row in User.select_many(db, "SELECT * FROM user WHERE birthday == DATE('now', 'localtime')"):
            with db:
                db.execute('UPDATE user SET balance=balance+100, birthday=? WHERE id=?',
                           [add_years(user_row.birthday, 1), user_row.id])
            user: discord.User = self.bot.get_user(user_row.id)
            announcement_channel: discord.TextChannel = self.bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
            await announcement_channel.send(f'🎉🎉🎉  Happy Birthday {user.mention}!  🎉🎉🎉'
                                            f'\nAs a present, you get 100 {CURRENCY}!')
            logger.info(f'gifted 100 to {user.name} as a birthday present!')

    @tasks.loop(hours=6)
    async def reward_media_consumption(self) -> AsyncIterator[Tuple[User, int]]:
        logger.debug('rewarding media consumption...')
        db = database.connect()

        async with aiohttp.ClientSession() as session:
            for user in User.select_many(db, "SELECT * FROM user WHERE mal_username > ''"):
                for content_type in ('anime', 'manga'):
                    content = await mal_rss.new_mal_content(db=db, session=session, content_type=content_type,
                                                            user_id=user.id, mal_username=user.mal_username)
                    with db:
                        for series_id, old_amount, consumed_amount in content:
                            reward = await mal_rss.calculate_reward(content_type, series_id,
                                                                    amount=consumed_amount - old_amount)
                            # todo move calculate_reward into Anime/Manga class(look for any if statements checking for
                            #  the content_type and move them there too)
                            db.execute('UPDATE user SET balance=balance+? WHERE id=?',
                                       (reward, user.id))
                            db.execute('REPLACE INTO consumed_media(user,type,id,amount) VALUES(?,?,?,?)',
                                       (user.id, content_type, series_id, consumed_amount))
                            logger.info(f'user {user.id} consumed {consumed_amount - old_amount}'
                                        f' bits of {series_id} ({content_type})')
                            yield user, reward

    @commands.cooldown(1, 60)
    @commands.command(aliases=['up'])
    async def update(self, ctx: Context):
        """Force a full update of everyone's earnings"""
        rewarded_money = await self.reward_media_consumption.coro(self)
        if rewarded_money:
            await ctx.info(title='Success!',
                           description='\n'.join(f"{ctx.bot.get_user(user.id).mention} earned {amount} {CURRENCY}"
                                                 for user, amount in rewarded_money))
        else:
            await ctx.info('Nothing changed...')

    @commands.command(aliases=['b'])
    async def balance(self, ctx: Context, user: Optional[discord.User] = None):
        """Get a user's balance"""
        user = user or ctx.author
        with database.connect() as db:
            user_data = User.select_one(db, 'SELECT * FROM user WHERE id=?', [user.id])
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


def add_years(date_: str, amount: int) -> str:
    return str(int(date_[:4]) + amount) + date_[4:]


def income_and_new_last_withdrawal(user: User) -> Tuple[int, datetime]:
    income_in_seconds = 3600 * 5
    last_withdrawal = datetime.fromisoformat(user.last_withdrawal)
    full_delta = datetime.today() - last_withdrawal
    full_income = int(full_delta.total_seconds() // income_in_seconds)
    rewarded_delta = timedelta(seconds=full_income * income_in_seconds)
    new_last_withdrawal = last_withdrawal + rewarded_delta
    income = min(full_income, 10)
    return income, new_last_withdrawal


def setup(bot: Shinobu):
    bot.add_cog(Economy(bot))
