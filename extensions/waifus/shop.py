from typing import Optional

import discord
from discord.ext import commands

from api.my_context import Context
from data.CONSTANTS import CURRENCY
from extensions.waifus import trade
from utils import database
from utils.formatting import paginate
from utils.waifus import buy_pack, CURRENT_PREDICATE, list_waifus, waifu_embed, \
    add_money, Refund, Upgrade, find_waifu


class WaifuShop(commands.Cog):
    @commands.group(aliases=['p'], invoke_without_command=True)
    async def pack(self, ctx: Context):
        """Get new waifus"""
        await ctx.send_help(ctx.command)

    @pack.command(name='list', aliases=['l'])
    async def pack_list(self, ctx: Context):
        """List all currently available packs"""
        with database.connect() as db:
            packs = db.execute(f'SELECT * FROM pack WHERE {CURRENT_PREDICATE}').fetchall()
        embed = discord.Embed(colour=discord.Colour.gold())
        for p in packs:
            end_date_str = f" (Available until {p['end_date']})" if p['end_date'] else ''
            embed.add_field(name=f"{p['name']} - {p['cost']} {CURRENCY}{end_date_str}",
                            value=p['description'], inline=False)
        await ctx.send(embed=embed)

    @pack.command(name='buy', aliases=['b'])
    @trade.forbid
    async def pack_buy(self, ctx: Context, pack_name: str):
        """Buy and open a pack"""
        db = database.connect()
        waifu, duplicate = await buy_pack(db, ctx.author.id, pack_name)
        embed = waifu_embed(waifu)

        if duplicate is not None:
            if isinstance(duplicate, Refund):
                duplicate_msg = f"Your duplicate waifu got refunded for {duplicate.amount} {CURRENCY}"
            else:  # isinstance(duplicate, Upgrade)
                duplicate_msg = f"Your waifu got upgraded to **{duplicate.upgraded_rarity.name}**!"
            embed.add_field(name='Duplicate', value=duplicate_msg)

        await ctx.send(embed=embed)

    @commands.group(aliases=['w'], invoke_without_command=True)
    async def waifu(self, ctx: Context):
        """Manage your waifus"""
        await ctx.send_help(ctx.command)

    @waifu.command(name='list', aliases=['l'])
    async def waifu_list(self, ctx: Context, user: Optional[discord.User] = None):
        """List all of your waifus"""
        user = user or ctx.author
        db = database.connect()
        waifus = list_waifus(db, user.id)
        padding = max(len(w.character.name) for w in waifus)
        waifu_str = '\n'.join(f"{w.character.name:<{padding}} - {w.rarity.name}" for w in waifus)
        await ctx.send_paginated(waifu_str, prefix='```md\n', suffix='```')

    @waifu.command(name='info', aliases=['i'])
    async def waifu_info(self, ctx: Context, *search_terms: str):
        """Get more information on a waifu"""
        with database.connect() as db:
            waifu = find_waifu(db, ctx.author.id, ' '.join(search_terms))
        await ctx.send(embed=waifu_embed(waifu))

    @waifu.command(name='refund', aliases=['r'])
    @trade.forbid
    async def waifu_refund(self, ctx: Context, *search_terms: str):
        """Get a refund for a waifu"""
        with database.connect() as db:
            waifu = find_waifu(db, ctx.author.id, ' '.join(search_terms))
            embed = waifu_embed(waifu)
            confirmation_msg = await ctx.send(
                f'Do you really want to get a refund for this waifu for {waifu.rarity.refund} {CURRENCY}?', embed=embed)
            if await ctx.confirm(confirmation_msg):
                add_money(db, ctx.author.id, waifu.rarity.refund)
                db.execute('DELETE FROM waifu WHERE id=?', [waifu.id])
                await ctx.info(f"Successfully refunded {waifu.character.name} for {waifu.rarity.refund} {CURRENCY}")
            else:
                await ctx.error('Cancelled refund.')

    @waifu.command(name='upgrade', aliases=['u', 'up'])
    @trade.forbid
    async def waifu_upgrade(self, ctx: Context, *search_terms: str):
        """Upgrade a waifu"""
        with database.connect() as db:
            waifu = find_waifu(db, ctx.author.id, ' '.join(search_terms))
            embed = waifu_embed(waifu)
            if waifu.rarity.upgrade_cost is None:
                return await ctx.error(f'This rarity is not upgradable:'
                                       f' **{waifu.rarity.name}** ({waifu.character.name})')
            confirmation_msg = await ctx.send(
                f'Do you really want to upgrade this waifu for {waifu.rarity.upgrade_cost} {CURRENCY}?',
                embed=embed
            )
            if await ctx.confirm(confirmation_msg):
                add_money(db, ctx.author.id, -waifu.rarity.upgrade_cost)
                db.execute('UPDATE waifu SET rarity=? WHERE id=?', [waifu.rarity.value + 1, waifu.id])
                await ctx.info('Success!')
            else:
                await ctx.error('Cancelled upgrade.')
