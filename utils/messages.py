import asyncio

import discord
from functools import partial
from typing import Optional, List


async def send_embed(color, messageable: discord.abc.Messageable,
                     description: Optional[str] = None, **kwargs):
    if description is not None:
        kwargs['description'] = description
    return await messageable.send(embed=discord.Embed(
        color=color, **kwargs)
    )


inform = partial(send_embed, discord.Color.green())
error = partial(send_embed, discord.Color.red())


async def confirm(bot: discord.Client, message: discord.Message, user: discord.User,
                  yes: str = '👍', no: str = '👎', timeout: int = 60) -> bool:
    def check(r, u):
        return r.message.id == message.id and u == user and str(r.emoji) in (yes, no)

    try:
        reaction, _ = await bot.wait_for('reaction_add', timeout=timeout, check=check)
    except asyncio.TimeoutError:
        return False
    return reaction.emoji == yes


async def confirm_multiuser(bot: discord.Client, message: discord.Message, users: List[discord.User],
                            yes: str = '👍', no: str = '👎', timeout: int = 60) -> bool:
    def check(r, u):
        return r.message.id == message.id and u in users and str(r.emoji) in (yes, no)

    while len(users) > 0:
        try:
            reaction, _ = await bot.wait_for('reaction_add', timeout=timeout, check=check)
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
