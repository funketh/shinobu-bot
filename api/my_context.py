import asyncio
from typing import Optional, Union, AsyncIterable, Set, Sequence, Tuple, Collection

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
            # TODO: checks description but complains about title ???
            raise ValueError('Title must be 256 or fewer in length')
        return await self.send(content, embed=discord.Embed(color=color, **kwargs))

    async def info(self, description: Optional[str] = None, content: Optional[str] = None, **kwargs):
        return await self.send_embed(discord.Color.green(), description, content, **kwargs)

    async def warn(self, description: Optional[str] = None, content: Optional[str] = None, **kwargs):
        return await self.send_embed(discord.Color.orange(), description, content, **kwargs)

    async def error(self, description: Optional[str] = None, content: Optional[str] = None, **kwargs):
        return await self.send_embed(discord.Color.red(), description, content, **kwargs)

    async def confirm(self, *args, **kwargs) -> bool:
        async for reaction, _ in self.wait_for_reactions(*args, reactions=(YES, NO), **kwargs):
            return reaction is not None and reaction.emoji == YES

    async def confirm_multiuser(self, msg: discord.Message, *, users: Set[discord.User], **kwargs) -> bool:
        async for reaction, _ in self.wait_for_reactions(msg, reactions=(YES, NO), users=users, **kwargs):
            if reaction.emoji == NO:
                return False
            if users.issubset(await reaction.users().flatten()):
                return True
        return False

    async def wait_for_reactions(self, msg: discord.Message, reactions: Collection[str], *,
                                 users: Collection[discord.User] = (), timeout: int = 300
                                 ) -> AsyncIterable[Tuple[discord.Reaction, discord.User]]:
        users = users or [self.author]
        for r in reactions:
            await msg.add_reaction(r)

        def any_user_answered(reaction: discord.Reaction, user: discord.User) -> bool:
            return (reaction.message.id == msg.id
                    and user in users
                    and str(reaction.emoji) in reactions)

        try:
            while True:
                try:
                    yield await self.bot.wait_for('reaction_add', timeout=timeout, check=any_user_answered)
                except asyncio.TimeoutError:
                    break

        finally:
            try:
                # Clear the reactions since clicking them no longer does anything
                for r in reactions:
                    await msg.clear_reaction(r)
            except discord.errors.NotFound:
                pass

    async def send_paginated(self, content: str, prefix: str = '', suffix: str = '', **kwargs):
        pages = list(paginate(content, prefix=prefix, suffix=suffix))
        await self.send_pager(pages, **kwargs)

    async def send_pager(self, pages: Sequence[str], *, users: Collection[discord.User] = (), timeout: int = 600):
        msg = await self.send(pages[0])

        if len(pages) == 1:
            return

        i = 0
        async for reaction, user in self.wait_for_reactions(msg, reactions=(UP, DOWN, PRINTER),
                                                            users=users, timeout=timeout):
            if reaction.emoji == PRINTER:
                await msg.delete()
                for p in pages:
                    await self.send(p)
                break

            elif reaction.emoji == UP:
                i = max(i - 1, 0)

            elif reaction.emoji == DOWN:
                i = min(i + 1, len(pages) - 1)

            await msg.edit(content=pages[i])
            await reaction.remove(user)
