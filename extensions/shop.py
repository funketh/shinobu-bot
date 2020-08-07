from typing import Optional, Union

import discord
from discord.ext import commands

from api.my_context import Context
from api.shinobu import Shinobu
from data.CONSTANTS import CURRENCY
from extensions import trade
from utils import database
from utils.database import Pack
from utils.waifus import buy_pack, CURRENT_PREDICATE, list_waifus, Refund, find_waifu, \
    waifu_interactions


class Shop(commands.Cog):
    @commands.command(aliases=['p'])
    @trade.forbid
    async def pack(self, ctx: Context, pack_name: Optional[str] = None):
        """Buy a pack with the given name. List all currently available packs if you don't give a pack name."""
        db = database.connect()

        if pack_name:
            waifu, duplicate = await buy_pack(db, ctx.author.id, pack_name)
            embed = waifu.to_embed()

            allow_interactions = True
            if duplicate is not None:
                if isinstance(duplicate, Refund):
                    duplicate_msg = f"Your duplicate waifu got refunded for {duplicate.amount} {CURRENCY}"
                    allow_interactions = False
                else:  # isinstance(duplicate, Upgrade)
                    duplicate_msg = f"Your waifu got upgraded to **{duplicate.upgraded_rarity.name}**!"
                embed.add_field(name='Duplicate', value=duplicate_msg)

            msg = await ctx.send(embed=embed)
            if allow_interactions:
                await waifu_interactions(ctx=ctx, db=db, msg=msg, waifu=waifu)

        else:
            packs = Pack.select_many(db, f'SELECT * FROM pack WHERE {CURRENT_PREDICATE}')

            embed = discord.Embed(colour=discord.Colour.gold())
            for p in packs:
                end_date_str = f" (Available until {p.end_date})" if p.end_date else ''
                embed.add_field(name=f"{p.name} - {p.cost} {CURRENCY}{end_date_str}", value=p.description, inline=False)

            await ctx.send(embed=embed)

    @staticmethod
    async def maybe_to_user(ctx: commands.Context, argument: str) -> Union[discord.User, str]:
        try:
            return await commands.UserConverter().convert(ctx, argument)
        except (commands.BadArgument, IndexError):
            # BadArgument -> string is not a user
            # IndexError -> string is empty
            return argument

    @commands.command(aliases=['w'])
    async def waifu(self, ctx: Context, user: str = '', *search_terms: str):
        """List waifus if you give no search terms. Otherwise display the waifu matching your query."""
        query = ' '.join(search_terms)
        maybe_user = await self.maybe_to_user(ctx, user)
        if isinstance(maybe_user, discord.User):
            user = maybe_user
        else:
            user = ctx.author
            query = maybe_user + query

        db = database.connect()

        if query:
            waifu = find_waifu(db, user.id, query)
            msg = await ctx.send(embed=waifu.to_embed())
            if user == ctx.author:
                await waifu_interactions(ctx=ctx, db=db, msg=msg, waifu=waifu)

        else:
            waifus = list_waifus(db, user.id)
            padding = max(len(w.character.name) for w in waifus)
            waifu_str = '\n'.join(f"{w.character.name:<{padding}} - {w.rarity.name}" for w in waifus)
            await ctx.send_paginated(waifu_str, prefix='```md\n', suffix='```')


def setup(bot: Shinobu):
    bot.add_cog(Shop())
