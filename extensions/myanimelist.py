import aiohttp
import discord
from discord.ext import commands
from typing import Optional

from shinobu import Shinobu
from utils.bing_search import search, first_match
from utils.myanimelist_scraper import Anime

class MyAnimeList(commands.Cog):
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command(name='anime', aliases=['ani', 'a'])
    async def anime_cmd(self, ctx: commands.Context, *search_terms: str):
        """Get information about an anime using myanimelist.net."""
        if len(search_terms) == 0:
            return await ctx.send('Please specify a search query.')

        series_id = await search_first_mal_id('anime', ' '.join(search_terms))
        if series_id is None:
            return await ctx.send("I couldn't find any results.")

        embed_msg = await ctx.send("*Getting the information from MyAnimeList.net...*")
        # score_msg = await ctx.send("*Loading scores...*")
        ctx.typing()

        scraper = await Anime.from_id(series_id)

        embed = discord.Embed()
        embed.colour = discord.Colour.dark_blue()
        embed.set_author(name=scraper.title, url=scraper.url)
        if scraper.thumbnail: embed.set_thumbnail(url=scraper.thumbnail)
        if scraper.score: embed.add_field(name='Score', value=scraper.score)
        if scraper.status: embed.add_field(name='Status', value=scraper.status)

        await embed_msg.edit(content=" ", embed=embed)


async def search_first_mal_id(domain_appendix: str, query: str) -> Optional[int]:
    async with aiohttp.ClientSession() as session:
        search_results = search(f'site:myanimelist.net/{domain_appendix} {query}', session)
        match = await first_match(rf'https://myanimelist\.net/{domain_appendix}/(\d+)/[^/]+', search_results)
    if match is not None:
        return int(match.group(1))

def setup(bot: Shinobu):
    bot.add_cog(MyAnimeList())
