import discord
import sqlite3
from discord.ext import commands
from typing import Optional

from shinobu import Shinobu
from utils import database
from utils.messages import error, inform


class Tags(commands.Cog):
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.content.startswith('!'):
            tag_name = message.content.lower()[1:]
            db = database.connect()
            value = db.execute('SELECT * FROM tag WHERE id=?', [tag_name]).fetchone()
            if value is not None:
                await message.channel.send(value)

    @commands.command(name='tag')
    async def tag_cmd(self, ctx: commands.Context, tag_name: str, message: Optional[discord.Message] = None):
        message = message or (await message.channel.history(limit=2).flatten())[1]
        db = database.connect()
        try:
            db.execute('INSERT INTO tag(name, value) VALUES(?, ?)', [tag_name, message.content])
        except sqlite3.IntegrityError:
            return await error(ctx, 'Tag already exists.')
        await inform(ctx, f'Successfully registered {tag_name}!')


def setup(bot: Shinobu):
    bot.add_cog(Tags())
