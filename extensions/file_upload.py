import aiohttp
import discord
import re
from discord.ext import commands
from mimetypes import guess_extension
from typing import Set

from shinobu import Shinobu
from utils import files, checks
from utils.files import tag_file


async def download(url: str) -> int:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await files.create_file(await response.read(), guess_extension(response.content_type) or '')


async def user_upload(user: discord.User, url: str) -> int:
    return await download(url)


@commands.command(name='upload', aliases=['up'])
async def upload_cmd(ctx: commands.Context):
    await user_upload(ctx.author, ctx.message.attachments[0].proxy_url)


def setup(bot: Shinobu):
    bot.add_command(upload_cmd)
