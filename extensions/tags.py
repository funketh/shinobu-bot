import discord
import sqlite3
from discord.ext import commands
from typing import Optional

from api.my_context import Context
from api.shinobu import Shinobu
from utils import database


class Tags(commands.Cog):
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.content.startswith('!'):
            key = message.content.lower()[1:]
            db = database.connect()
            value, = db.execute('SELECT value FROM tag WHERE key=?', [key]).fetchone() or [None]
            if value is not None:
                await message.channel.send(value[0])

    @commands.command(name='tag')
    async def tag_cmd(self, ctx: Context, key: str, message: Optional[discord.Message] = None):
        """Register a message under a key (access it by typing !<key>)"""
        message = message or (await ctx.history(limit=2).flatten())[1]
        db = database.connect()
        with db:
            try:
                db.execute('INSERT INTO tag(key, value) VALUES(?, ?)', [key, message.content])
            except sqlite3.IntegrityError:
                return await ctx.error('Tag already exists.')
        await ctx.inform(f'Successfully registered {key}!')


def setup(bot: Shinobu):
    bot.add_cog(Tags())
