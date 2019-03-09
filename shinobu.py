import aiosqlite
import discord
import logging
from discord.ext.commands import Bot, Context

from CONSTANTS import DB_PATH


async def extension_modules():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT module_path FROM extension WHERE active=1') as cursor:
            async for row in cursor:
                yield row[0]


class Shinobu(Bot):
    async def load_all_extensions(self):
        async for ext in extension_modules():
            self.load_extension(ext)

    async def _unload_all_extensions(self):
        async for ext in extension_modules():
            self.unload_extension(ext)

    async def reload_all_extensions(self):
        await self._unload_all_extensions()
        await self.load_all_extensions()

    async def on_ready(self):
        await self.load_all_extensions()
        logging.info('Logged on as {0}!'.format(self.user))

    async def on_command_error(self, context: Context, exception: Exception):
        logging.exception(exception)