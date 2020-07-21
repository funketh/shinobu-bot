import asyncio
from typing import Optional, Union, Iterable, AsyncIterable, Set, Sequence

import discord
from discord import Color
from discord.ext import commands

from data.CONSTANTS import NO, YES, PRINTER, DOWN, UP
from utils.formatting import paginate


class Context(commands.Context):
    async def send_embed(self, color: Union[Color, int], description: Optional[str] = None,
                         content: Optional[str] = None, **kwargs):
        if description is not None:
            kwargs['description'] = description
        if len(kwargs['description']) > 256:
            raise ValueError('Title must be 256 or fewer in length')
        return await self.send(content, embed=discord.Embed(color=color, **kwargs))

    async def info(self, description: Optional[str] = None, content: Optional[str] = None, **kwargs):
        return await self.send_embed(discord.Color.green(), description, content, **kwargs)

    async def warn(self, description: Optional[str] = None, content: Optional[str] = None, **kwargs):
        return await self.send_embed(discord.Color.orange(), description, content, **kwargs)

    async def error(self, description: Optional[str] = None, content: Optional[str] = None, **kwargs):
        return await self.send_embed(discord.Color.red(), description, content, **kwargs)

    async def confirm(self, *args, **kwargs) -> bool:
        reaction = await self.wait_for_reaction(*args, reactions=(YES, NO), **kwargs)
        return reaction.emoji == YES

    async def confirm_multiuser(self, msg: discord.Message, users: Set[discord.User], **kwargs) -> bool:
        async for reaction in self.wait_for_reactions(msg, reactions=(YES, NO), users=users, **kwargs):
            if reaction.emoji == NO:
                return False
            if users.issubset(await reaction.users().flatten()):
                return True
        return False

    async def wait_for_reaction(self, msg: discord.Message, reactions: Iterable[str],
                                user: Optional[discord.User] = None, **kwargs) -> Optional[discord.Reaction]:
        user = user or self.author
        async for reaction in self.wait_for_reactions(msg, reactions, [user], **kwargs):
            return reaction

    async def wait_for_reactions(self, msg: discord.Message, reactions: Iterable[str],
                                 users: Iterable[discord.User] = (), timeout=60) -> AsyncIterable[discord.Reaction]:
        users = users or [self.author]
        for r in reactions:
            await msg.add_reaction(r)

        def any_user_answered(r: discord.Reaction, u: discord.User):
            return r.message.id == msg.id and u in users and str(r.emoji) in reactions

        while True:
            try:
                reaction, _ = await self.bot.wait_for('reaction_add', timeout=timeout, check=any_user_answered)
            except asyncio.TimeoutError:
                break
            yield reaction

    async def send_paginated(self, content: str, prefix: str = '', suffix: str = '', **kwargs):
        pages = list(paginate(content, prefix=prefix, suffix=suffix))
        await self.send_pager(pages, **kwargs)

    async def send_pager(self, pages: Sequence[str], *, timeout=600, **kwargs):
        msg = await self.send(pages[0])

        if len(pages) == 1:
            return

        i = 0
        async for reaction in self.wait_for_reactions(msg, reactions=(UP, DOWN, PRINTER), timeout=timeout, **kwargs):
            if reaction.emoji == PRINTER:
                await msg.delete()
                for p in pages:
                    await self.send(p)
                return

            if reaction.emoji == UP:
                i = max(i-1, 0)
            elif reaction.emoji == DOWN:
                i = min(i+1, len(pages)-1)

            await msg.edit(content=pages[i])
            async for u in reaction.users():
                if u != self.bot.user:
                    await reaction.remove(u)
