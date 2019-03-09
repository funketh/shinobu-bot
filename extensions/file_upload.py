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


async def image_of_the_day(message: discord.Message):
    if message.author.bot or not message.guild:
        return
    # TODO
    # if await checks.has_role(message.author, ManOfCulture):
    if True:
        pattern_tags = {
            re.compile("of (the|this) day.*?:", re.IGNORECASE): {'RndImg'},
            re.compile("compensation.*?:", re.IGNORECASE): {'RndImg', 'Compensation'},
            re.compile("bonus.*?:", re.IGNORECASE): {'RndImg', 'Bonus'},
        }
        tags = set.union(*(tags for pattern, tags in pattern_tags.items() if pattern.search(message.content)))
        if len(tags) == 0:
            return

        if not message.attachments:
            message = await message.channel.wait_for_message(author=message.author, timeout=300)
        try:
            url = message.attachments[0].url
        except (IndexError, AttributeError):
            return
        file_id = await user_upload(message.author, url)
        await tag_file(file_id, tags)


def setup(bot: Shinobu):
    bot.add_listener(image_of_the_day, 'on_message')
    bot.add_command(upload_cmd)