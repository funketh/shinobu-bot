import asyncio

import discord
from discord import Color
from discord.ext import commands
from typing import Optional, List, Union

from utils.formatting import paginate


class Context(commands.Context):
    async def send_embed(self, color: Union[Color, int], description: Optional[str] = None,
                         content: Optional[str] = None, **kwargs):
        if description is not None:
            kwargs['description'] = description
        if len(kwargs['description']) > 256:
            raise ValueError('Title must be 256 or fewer in length')
        return await self.send(content, embed=discord.Embed(color=color, **kwargs))

    async def send_paginated(self, content, *, prefix: str = '', suffix: str = '', **kwargs):
        for p in paginate(content, prefix, suffix):
            await self.send(p, **kwargs)

    async def info(self, description: Optional[str] = None, content: Optional[str] = None, **kwargs):
        return await self.send_embed(discord.Color.green(), description, content, **kwargs)

    async def warn(self, description: Optional[str] = None, content: Optional[str] = None, **kwargs):
        return await self.send_embed(discord.Color.orange(), description, content, **kwargs)

    async def error(self, description: Optional[str] = None, content: Optional[str] = None, **kwargs):
        return await self.send_embed(discord.Color.red(), description, content, **kwargs)

    async def confirm(self, message: discord.Message, user: Optional[discord.User] = None,
                      yes: str = '👍', no: str = '👎', timeout: int = 60) -> bool:
        user = user or self.author
        await message.add_reaction(yes)
        await message.add_reaction(no)

        def user_answered(r: discord.Reaction, u: discord.User):
            return r.message.id == message.id and u == user and str(r.emoji) in (yes, no)

        try:
            reaction, _ = await self.bot.wait_for('reaction_add', timeout=timeout, check=user_answered)
        except asyncio.TimeoutError:
            return False
        return reaction.emoji == yes

    async def confirm_multiuser(self, message: discord.Message, users: List[discord.User],
                                yes: str = '👍', no: str = '👎', timeout: int = 60) -> bool:
        await message.add_reaction(yes)
        await message.add_reaction(no)

        def any_user_answered(r: discord.Reaction, u: discord.User):
            return r.message.id == message.id and u in users and str(r.emoji) in (yes, no)

        while len(users) > 0:
            try:
                reaction, _ = await self.bot.wait_for('reaction_add', timeout=timeout, check=any_user_answered)
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
