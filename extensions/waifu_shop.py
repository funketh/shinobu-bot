import asyncio
import sqlite3

import discord
from discord.ext import commands
from fuzzywuzzy import process
from typing import Optional, List

from CONSTANTS import CURRENCY, CMD_PREFIX
from shinobu import Shinobu
from utils import database
from utils.database import DB
from utils.shop import buy_pack, CURRENT_PREDICATE, NotEnoughMoney, UnknownPackName, refund, add_money


class WaifuShop(commands.Cog):
    @commands.command(name='pack_list', aliases=['pl'])
    async def list_packs_cmd(self, ctx: commands.Context):
        """Lists all currently available packs"""
        db = database.connect()
        packs = db.execute(f'SELECT * FROM pack WHERE {CURRENT_PREDICATE}').fetchall()
        embed = discord.Embed(colour=discord.Colour.gold())
        for p in packs:
            end_date_str = f" (Available until {p['end_date']})" if p['end_date'] else ''
            embed.add_field(name=f"{p['name']} - {p['cost']}{CURRENCY}{end_date_str}",
                            value=p['description'], inline=False)
        await ctx.send(embed=embed)

    @commands.command(name='pack_buy', aliases=['pb'])
    async def pack_buy_cmd(self, ctx: commands.Context, pack_name: str):
        """Buy and open a pack"""
        db = database.connect()
        try:
            receipt = await buy_pack(db, ctx.author.id, pack_name)
        except NotEnoughMoney:
            return await ctx.send("You don't have enough money to buy that pack!")
        except UnknownPackName:
            return await ctx.send(f"Unknown pack name. Type `{CMD_PREFIX}{self.list_packs_cmd.name}` "
                                  f"for a list of available packs.")
        embed = waifu_embed(name=receipt.character['name'], series=receipt.character['series'],
                            image_url=receipt.character['image_url'], rarity_name=receipt.rarity['name'],
                            rarity_color=receipt.rarity['colour'])
        if receipt.old_rarity is not None:
            if receipt.refund is None:
                embed.add_field(name='Duplicate', value='Your waifu was upgraded!')
            else:
                embed.add_field(name='Duplicate',
                                value=f'Your duplicate waifu was refunded for {receipt.refund}{CURRENCY}!')
        await ctx.send(embed=embed)

    @commands.command(name='waifu_list', aliases=['wl'])
    async def waifu_list_cmd(self, ctx: commands.Context, user: Optional[discord.User] = None):
        """Lists all of your waifus"""
        user = user or ctx.author
        db = database.connect()
        waifus = list_waifus(db, user.id)
        waifus.sort(key=lambda w: (w['rarity.name'], w['name']))
        padding = max(len(w['name']) for w in waifus)
        waifu_str = '\n'.join(f"{w['name']:<{padding}} - {w['rarity.name']}" for w in waifus)
        waifu_codeblock = f'```md\n{waifu_str}\n```'
        await ctx.send(waifu_codeblock)  # todo split into pages

    @commands.command(name='waifu_info', aliases=['wi'])
    async def waifu_info_cmd(self, ctx: commands.Context, *search_terms: str):
        """Get more information on one of your waifus"""
        db = database.connect()
        waifus = list_waifus(db, ctx.author.id)
        chosen_name: str = process.extractOne(' '.join(search_terms), (w['name'] for w in waifus))[0]
        waifu = next(w for w in waifus if w['name'] == chosen_name)
        await ctx.send(embed=waifu_embed(name=waifu['name'], series=waifu['series'], image_url=waifu['image_url'],
                                         rarity_name=waifu['rarity.name'], rarity_color=waifu['rarity.colour']))

    @commands.command(name='waifu_refund', aliases=['wr'])
    async def waifu_refund_cmd(self, ctx: commands.Context, *search_terms: str):
        """Get a refund for one of your waifus"""
        db = database.connect()
        with db:
            waifus = list_waifus(db, ctx.author.id)
            chosen_name: str = process.extractOne(' '.join(search_terms), (w['name'] for w in waifus))[0]
            waifu = next(w for w in waifus if w['name'] == chosen_name)
            await ctx.send('Do you really want to get a refund for this waifu? (React with 👍 or 👎)',
                           embed=waifu_embed(name=waifu['name'], series=waifu['series'], image_url=waifu['image_url'],
                                             rarity_name=waifu['rarity.name'], rarity_color=waifu['rarity.colour']))
            try:
                reaction, user = await ctx.bot.wait_for('reaction_add', timeout=60.0,
                                                        check=lambda r, u: u == ctx.author and str(r.emoji) in '👍👎')
                if reaction.emoji == '👎':
                    raise ValueError
            except (asyncio.TimeoutError, ValueError):
                await ctx.send('Cancelled refund.')
            else:
                refund_amount = refund(db, ctx.author.id, waifu['rarity.value'], 1)
                db.execute('DELETE FROM waifu WHERE id=?', [waifu['waifu.id']])
                add_money(db, ctx.author.id, refund_amount)
                await ctx.send(f"Successfully refunded {waifu['name']}"
                               f"for {refund_amount} {CURRENCY}")


def list_waifus(db: DB, user_id: int) -> List[sqlite3.Row]:
    return db.execute("""
    SELECT waifu.id AS "waifu.id",
           character.name, character.image_url, character.series,
           rarity.name AS "rarity.name", rarity.colour AS "rarity.colour", rarity.value AS "rarity.value"
    FROM waifu
    JOIN character ON character.id = waifu.character
    JOIN rarity ON rarity.value = waifu.rarity
    WHERE waifu.user=?
    ORDER BY rarity.value DESC, character.name ASC
    """, [user_id]).fetchall()


def waifu_embed(name, series, image_url, rarity_name, rarity_color):
    embed = discord.Embed(color=rarity_color, title=f'{name} [{series}]',
                          description=f"**{rarity_name}**")
    if image_url:
        embed.set_image(url=image_url)
    return embed


def setup(bot: Shinobu):
    bot.add_cog(WaifuShop())
