from functools import partial

import discord
from typing import Optional


async def send_embed(color, messageable: discord.abc.Messageable,
                     description: Optional[str] = None, **kwargs):
    if description is not None:
        kwargs['description'] = description
    return await messageable.send(embed=discord.Embed(
        color=color, **kwargs)
    )

inform = partial(send_embed, discord.Color.green())
