import discord
from discord.ext import commands
from typing import Optional

from api.my_context import Context
from api.shinobu import Shinobu
from data.CONSTANTS import CURRENCY, CMD_PREFIX
from extensions import waifu_transactions
from utils import database
from utils.waifus import buy_pack, CURRENT_PREDICATE, NotEnoughMoney, UnknownPackName, refund, find_waifus, \
    list_waifus, waifu_embed


class WaifuShop(commands.Cog):
    @commands.group(aliases=['p'], invoke_without_command=True)
    async def pack(self, ctx: Context):
        """Get new waifus"""
        await ctx.send_help(ctx.command)

    @pack.command(name='list', aliases=['l'])
    async def pack_list(self, ctx: Context):
        """Lists all currently available packs"""
        db = database.connect()
        packs = db.execute(f'SELECT * FROM pack WHERE {CURRENT_PREDICATE}').fetchall()
        embed = discord.Embed(colour=discord.Colour.gold())
        for p in packs:
            end_date_str = f" (Available until {p['end_date']})" if p['end_date'] else ''
            embed.add_field(name=f"{p['name']} - {p['cost']} {CURRENCY}{end_date_str}",
                            value=p['description'], inline=False)
        await ctx.send(embed=embed)

    @pack.command(name='buy', aliases=['b'])
    @waifu_transactions.forbid
    async def pack_buy(self, ctx: Context, pack_name: str):
        """Buy and open a pack"""
        db = database.connect()
        try:
            waifu, old_rarity_val, refund_amount = await buy_pack(db, ctx.author.id, pack_name)
        except NotEnoughMoney:
            return await ctx.error("You don't have enough money to buy that pack!")
        except UnknownPackName:
            return await ctx.error(f"Unknown pack name. Type `{CMD_PREFIX}{self.pack_list.name}` "
                                   f"for a list of available packs.")
        embed = waifu_embed(waifu)
        if old_rarity_val is not None:
            embed.add_field(name='Duplicate',
                            value=f"Your {'older ' if old_rarity_val > waifu.rarity.value else ''}"
                                  f"duplicate waifu got refunded for {refund_amount} {CURRENCY}")
        await ctx.send(embed=embed)

    @commands.group(aliases=['w'], invoke_without_command=True)
    async def waifu(self, ctx: Context):
        """Manage your waifus"""
        await ctx.send_help(ctx.command)

    @waifu.command(name='list', aliases=['l'])
    async def waifu_list(self, ctx: Context, user: Optional[discord.User] = None):
        """Lists all of your waifus"""
        user = user or ctx.author
        db = database.connect()
        waifus = list_waifus(db, user.id)
        padding = max(len(w.character.name) for w in waifus)
        waifu_str = '\n'.join(f"{w.character.name:<{padding}} - {w.rarity.name}" for w in waifus)
        waifu_codeblock = f'```md\n{waifu_str}\n```'
        await ctx.send(waifu_codeblock)  # todo split into pages

    @waifu.command(name='info', aliases=['i'])
    async def waifu_info(self, ctx: Context, *search_terms: str):
        """Get more information on one of your waifus"""
        db = database.connect()
        try:
            waifu = next(find_waifus(db, ctx.author.id, ' '.join(search_terms)))
        except StopIteration:
            return await ctx.error("You don't have any waifus!")
        await ctx.send(embed=waifu_embed(waifu))

    @waifu.command(name='refund', aliases=['r'])
    @waifu_transactions.forbid
    async def waifu_refund(self, ctx: Context, *search_terms: str):
        """Get a refund for one of your waifus"""
        db = database.connect()
        with db:
            try:
                waifu = next(find_waifus(db, ctx.author.id, ' '.join(search_terms)))
            except StopIteration:
                return await ctx.error("You don't have any waifus!")
            embed = waifu_embed(waifu)
            confirmation_msg = await ctx.send(
                'Do you really want to get a refund for this waifu? (React with 👍 or 👎)', embed=embed)
            if await ctx.confirm(confirmation_msg):
                refund_amount = refund(db, ctx.author.id, waifu.rarity.value, 10)
                db.execute('DELETE FROM waifu WHERE id=?', [waifu.id])
                await ctx.info(f"Successfully refunded {waifu.character.name} for {refund_amount} {CURRENCY}")
            else:
                await ctx.error('Cancelled refund.')


def setup(bot: Shinobu):
    bot.add_cog(WaifuShop())
