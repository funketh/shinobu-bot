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
    @commands.group(aliases=['p'], invoke_without_command=True)
    async def pack(self, ctx: Context):
        """Get new waifus"""
        await ctx.send_help(ctx.command)

    @pack.command(name='list', aliases=['l'])
    async def pack_list(self, ctx: Context):
        """List all currently available packs"""
        db = database.connect()
        packs = Pack.select_many(db, f'SELECT * FROM pack WHERE {CURRENT_PREDICATE}')

        embed = discord.Embed(colour=discord.Colour.gold())
        for p in packs:
            end_date_str = f" (Available until {p.end_date})" if p.end_date else ''
            embed.add_field(name=f"{p.name} - {p.cost} {CURRENCY}{end_date_str}", value=p.description, inline=False)

        await ctx.send(embed=embed)

    @pack.command(name='buy', aliases=['b'])
    @trade.forbid
    async def pack_buy(self, ctx: Context, pack_name: str):
        """Buy and open a pack"""
        db = database.connect()
        waifu, duplicate = await buy_pack(db, ctx.author.id, pack_name)
        embed = waifu.to_embed()

        if duplicate is not None:
            if isinstance(duplicate, Refund):
                duplicate_msg = f"Your duplicate waifu got refunded for {duplicate.amount} {CURRENCY}"
            else:  # isinstance(duplicate, Upgrade)
                duplicate_msg = f"Your waifu got upgraded to **{duplicate.upgraded_rarity.name}**!"
            embed.add_field(name='Duplicate', value=duplicate_msg)

        msg = await ctx.send(embed=embed)
        await waifu_interactions(ctx=ctx, db=db, msg=msg, waifu=waifu)

    class UserOrStringConverter(commands.UserConverter):
        async def convert(self, ctx: Context, argument: str) -> Union[discord.User, str]:
            try:
                return await super().convert(ctx, argument)
            except commands.BadArgument:
                return argument

    @commands.command(aliases=['w'])
    async def waifu(self, ctx: Context, user: Optional[UserOrStringConverter] = None, *search_terms: str):
        """List waifus if you give no search terms. Otherwise display the waifu matching your query."""
        if not isinstance(user, discord.User):
            if isinstance(user, str):
                search_terms = (user, *search_terms)
            user = ctx.author

        db = database.connect()

        if search_terms:
            waifu = find_waifu(db, user.id, ' '.join(search_terms))
            msg = await ctx.send(embed=waifu.to_embed())
            await waifu_interactions(ctx=ctx, db=db, msg=msg, waifu=waifu)

        else:
            waifus = list_waifus(db, user.id)
            padding = max(len(w.character.name) for w in waifus)
            waifu_str = '\n'.join(f"{w.character.name:<{padding}} - {w.rarity.name}" for w in waifus)
            await ctx.send_paginated(waifu_str, prefix='```md\n', suffix='```')


def setup(bot: Shinobu):
    bot.add_cog(Shop())
