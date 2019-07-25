import discord
import logging
import os
import re
import traceback
from discord.ext import commands

from api.my_context import Context
from utils import database


class Shinobu(commands.Bot):

    def __init__(self, command_prefix, **options):
        super().__init__(command_prefix, **options)

    @staticmethod
    async def _extension_modules():
        ext = 'extensions'
        for file_name in os.listdir(ext):
            if file_name.endswith('.py'):
                yield f'{ext}.{file_name[:-3]}'

    async def reload_all_extensions(self):
        async for ext in self._extension_modules():
            try:
                self.reload_extension(ext)
            except commands.ExtensionNotLoaded:
                self.load_extension(ext)

    async def update_user_database(self):
        db = database.connect()
        with db:
            db.executemany('INSERT OR IGNORE INTO user(id) VALUES(?)',
                           [[m.id] for g in self.guilds for m in g.members])

    async def on_member_join(self, _: discord.Member):
        await self.update_user_database()

    async def on_ready(self):
        await self.reload_all_extensions()
        logging.info(f'Logged on as {self.user}!')
        await self.update_user_database()

    async def on_command_error(self, ctx: Context, exception: Exception):
        cog = ctx.cog
        if (self.extra_events.get('on_command_error', None)
                or hasattr(ctx.command, 'on_error')
                or (cog and cog._get_overridden_method(cog.cog_command_error) is not None)
                or isinstance(exception, commands.CommandNotFound)):
            return
        await ctx.error(re.sub(
            '.*?(\w+?:.*)',
            lambda m: m.group(1),
            traceback.format_exception_only(type(exception), exception)[-1]
        ))
        logging.info(f'Ignoring exception in command {ctx.command}:\n'
                     + ''.join(traceback.format_exception(type(exception), exception, exception.__traceback__)))

    async def get_context(self, message, *, cls=Context):
        return await super().get_context(message, cls=cls)
