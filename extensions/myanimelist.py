from collections import Collection
from typing import Optional

import aiohttp
from discord.ext import commands

from api.expected_errors import ExpectedCommandError
from api.my_context import Context
from api.shinobu import Shinobu
from utils.bing_search import search, first_match
from utils.mal_scraper import Anime, Manga, Content


class MyAnimeList(commands.Cog):
    @commands.cooldown(2, 10, commands.BucketType.user)
    @commands.command(aliases=['a'])
    async def anime(self, ctx: Context, *search_terms: str):
        """Get information about an anime using myanimelist.net"""
        await find_series(ctx, search_terms, content_type=Anime)

    @commands.cooldown(2, 10, commands.BucketType.user)
    @commands.command(aliases=['m'])
    async def manga(self, ctx: Context, *search_terms: str):
        """Get information about a manga using myanimelist.net"""
        await find_series(ctx, search_terms, content_type=Manga)


async def find_series(ctx: Context, search_terms: Collection[str], content_type: type[Content]):
    if len(search_terms) == 0:
        raise ExpectedCommandError('Please specify a search query.')

    series_id = await search_first_mal_id(content_type.domain_suffix, ' '.join(search_terms))
    if series_id is None:
        raise ExpectedCommandError("I couldn't find any results.")

    embed_msg = await ctx.send("*Getting the information from MyAnimeList.net...*")
    async with ctx.typing():
        scraper = content_type.from_id(series_id)
        embed = await scraper.to_embed()
        await embed_msg.edit(content=" ", embed=embed)


async def search_first_mal_id(domain_suffix: str, query: str) -> Optional[int]:
    async with aiohttp.ClientSession() as session:
        search_results = search(f'site:myanimelist.net/{domain_suffix} {query}', session)
        match = await first_match(rf'https://myanimelist\.net/{domain_suffix}/(\d+)/[^/]+', search_results)
    if match:
        return int(match.group(1))


def setup(bot: Shinobu):
    bot.add_cog(MyAnimeList())
