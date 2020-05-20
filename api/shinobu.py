import logging
import os
import re
import traceback

import discord
from discord.ext import commands

from api.expected_errors import ExpectedCommandError
from api.my_context import Context
from utils import database


class Shinobu(commands.Bot):
    @staticmethod
    async def _extension_modules():
        ext = 'extensions'
        for path in os.listdir(ext):
            if path.endswith('.py'):
                yield f'{ext}.{path[:-3]}'
            elif os.path.isdir(f'{ext}/{path}') and path != '__pycache__':
                yield f'{ext}.{path}'

    async def reload_all_extensions(self):
        async for ext in self._extension_modules():
            try:
                self.reload_extension(ext)
            except commands.ExtensionNotLoaded:
                self.load_extension(ext)

    async def update_user_database(self):
        with database.connect() as db:
            db.executemany('INSERT OR IGNORE INTO user(id) VALUES(?)',
                           [[m.id] for g in self.guilds for m in g.members])

    async def on_member_join(self, _: discord.Member):
        await self.update_user_database()

    async def on_ready(self):
        await self.update_user_database()
        await self.reload_all_extensions()
        logging.info(f'Logged on as {self.user}!')

    async def on_command_error(self, ctx: Context, exception: Exception):
        if (self.extra_events.get('on_command_error', None)
                or hasattr(ctx.command, 'on_error')
                or (ctx.cog and ctx.cog._get_overridden_method(ctx.cog.cog_command_error) is not None)
                or isinstance(exception, commands.CommandNotFound)):
            return

        if isinstance(exception, commands.CommandInvokeError):
            # "unbox" errors produced while invoking a command
            exception = exception.original

        if isinstance(exception, ExpectedCommandError):
            # if the error was expected then simply send the exception message to the user
            await ctx.error(exception.message)
        else:
            await ctx.error(re.sub(r'.*?(\w+?:.*)',
                                   lambda m: m.group(1),
                                   traceback.format_exception_only(type(exception), exception)[-1]))
            logging.info(f'Ignoring exception in command {ctx.command}:\n'
                         + ''.join(traceback.format_exception(type(exception), exception, exception.__traceback__)))

    async def get_context(self, message, *, cls=Context):
        return await super().get_context(message, cls=cls)
