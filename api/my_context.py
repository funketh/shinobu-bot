import asyncio

import discord
from discord import Color
from discord.ext import commands
from typing import Optional, List, Union


class Context(commands.Context):
    async def send_embed(self, color: Union[Color, int], title: Optional[str] = None,
                         content: Optional[str] = None, **kwargs):
        if title is not None:
            kwargs['title'] = title
        if len(kwargs['title']) > 256:
            raise ValueError('title must be 256 or fewer in length')
        return await self.send(content, embed=discord.Embed(color=color, **kwargs))

    async def inform(self, title: Optional[str] = None, content: Optional[str] = None, **kwargs):
        return await self.send_embed(discord.Color.green(), title, content, **kwargs)

    async def error(self, title: Optional[str] = None, content: Optional[str] = None, **kwargs):
        return await self.send_embed(discord.Color.red(), title, content, **kwargs)

    async def confirm(self, message: discord.Message, user: Optional[discord.User] = None,
                      yes: str = '👍', no: str = '👎', timeout: int = 60) -> bool:
        user = user or self.author
        check = lambda r, u: r.message.id == message.id and u == user and str(r.emoji) in (yes, no)
        try:
            reaction, _ = await self.bot.wait_for('reaction_add', timeout=timeout, check=check)
        except asyncio.TimeoutError:
            return False
        return reaction.emoji == yes

    async def confirm_multiuser(self, message: discord.Message, users: List[discord.User],
                                yes: str = '👍', no: str = '👎', timeout: int = 60) -> bool:
        check = lambda r, u: r.message.id == message.id and u in users and str(r.emoji) in (yes, no)

        while len(users) > 0:
            try:
                reaction, _ = await self.bot.wait_for('reaction_add', timeout=timeout, check=check)
            except asyncio.TimeoutError:
                return False
            if reaction.emoji == no:
                return False
            for u in await reaction.users().flatten():
                try:
                    users.remove(u)
                except ValueError:
                    pass
        return True
