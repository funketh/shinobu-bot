import discord
from discord.ext import commands

from CONSTANTS import CURRENCY, CMD_PREFIX
from utils.shop import buy_pack, CURRENT_PREDICATE, NotEnoughMoney, UnknownPackName
from shinobu import Shinobu
from utils import database

class WaifuShop(commands.Cog):
    @commands.command(name='packs', aliases=['lp'])
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

    @commands.command(name='buy_pack', aliases=['bp'])
    async def buy_pack_cmd(self, ctx: commands.Context, pack_name: str):
        """Buy and open a pack"""
        db = database.connect()
        try:
            receipt = await buy_pack(db, ctx.author.id, pack_name)
        except NotEnoughMoney:
            return await ctx.send("You don't have enough money to buy that pack!")
        except UnknownPackName:
            return await ctx.send(f"Unknown pack name. Type `{CMD_PREFIX}{self.list_packs_cmd.name}` "
                                  f"for a list of available packs.")
        embed = discord.Embed(colour=receipt.rarity['colour'], title=receipt.character['name'],
                              description=f"**{receipt.rarity['name']}**")
        if receipt.character['image_url']:
            embed.set_image(url=receipt.character['image_url'])
        if receipt.old_rarity is not None:
            if receipt.refund is None:
                embed.add_field(name='Duplicate', value='Your waifu was upgraded!')
            else:
                embed.add_field(name='Duplicate', value=f'Your duplicate waifu was refunded for {receipt.refund}{CURRENCY}!')
        await ctx.send(embed=embed)

    @commands.command(name='waifus', aliases=['lw'])
    async def list_waifus_cmd(self, ctx: commands.Context):
        """Lists all of your waifus"""
        db = database.connect()
        waifus = db.execute("""
        SELECT character.name AS name, rarity.name AS rarity FROM waifu
        JOIN character    ON character.id = waifu.character
        JOIN rarity     ON rarity.value = waifu.rarity
        WHERE waifu.user=?
        ORDER BY character.name
        """, [ctx.author.id]).fetchall()
        waifus.sort(key=lambda w: (w['rarity'], w['name']))
        padding = max(len(w['name']) for w in waifus)
        waifu_str = '\n'.join(f"{w['name']:<{padding}} - {w['rarity']}" for w in waifus)
        waifu_codeblock = f'```md\n{waifu_str}\n```'
        await ctx.send(waifu_codeblock)  # todo split into pages

def setup(bot: Shinobu):
    bot.add_cog(WaifuShop())
