import discord
import logging
import os
from discord.ext.commands import Bot, ExtensionNotLoaded


class Shinobu(Bot):
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
            except ExtensionNotLoaded:
                self.load_extension(ext)

    async def on_ready(self):
        await self.reload_all_extensions()
        logging.info(f'Logged on as {self.user}!')
