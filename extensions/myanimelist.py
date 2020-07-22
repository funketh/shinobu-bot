from typing import Optional, Collection

import aiohttp
import discord
from discord.ext import commands

from api.expected_errors import ExpectedCommandError
from api.my_context import Context
from api.shinobu import Shinobu
from utils.bing_search import search, first_match
from utils.mal_scraper import Anime, Manga


class MyAnimeList(commands.Cog):
    @commands.cooldown(2, 10, commands.BucketType.user)
    @commands.command(aliases=['a'])
    async def anime(self, ctx: Context, *search_terms: str):
        """Get information about an anime using myanimelist.net"""
        await find_series(ctx, search_terms, content_type='anime')

    @commands.cooldown(2, 10, commands.BucketType.user)
    @commands.command(aliases=['m'])
    async def manga(self, ctx: Context, *search_terms: str):
        """Get information about a manga using myanimelist.net"""
        await find_series(ctx, search_terms, content_type='manga')


async def find_series(ctx: Context, search_terms: Collection[str], content_type: str):
    if content_type == 'anime':
        scraper_class = Anime
    elif content_type == 'manga':
        scraper_class = Manga
    else:
        raise ValueError(f'unknown {content_type=}')

    if len(search_terms) == 0:
        raise ExpectedCommandError('Please specify a search query.')

    series_id = await search_first_mal_id(content_type, ' '.join(search_terms))
    if series_id is None:
        raise ExpectedCommandError("I couldn't find any results.")

    embed_msg = await ctx.send("*Getting the information from MyAnimeList.net...*")
    ctx.typing()

    scraper = await scraper_class.from_id(series_id)
    embed = discord.Embed()
    embed.colour = discord.Colour.dark_blue()
    embed.set_author(name=scraper.title, url=scraper.url)
    if scraper.thumbnail:
        embed.set_thumbnail(url=scraper.thumbnail)
    if scraper.score:
        embed.add_field(name='Score', value=scraper.score)
    if scraper.status:
        embed.add_field(name='Status', value=scraper.status)

    if content_type == 'manga':
        if scraper.volumes:
            embed.add_field(name='Volumes', value=scraper.volumes)
        if scraper.chapters:
            embed.add_field(name='Chapters', value=scraper.chapters)

    await embed_msg.edit(content=" ", embed=embed)


async def search_first_mal_id(domain_suffix: str, query: str) -> Optional[int]:
    async with aiohttp.ClientSession() as session:
        search_results = search(f'site:myanimelist.net/{domain_suffix} {query}', session)
        match = await first_match(rf'https://myanimelist\.net/{domain_suffix}/(\d+)/[^/]+', search_results)
    if match:
        return int(match.group(1))


def setup(bot: Shinobu):
    bot.add_cog(MyAnimeList())
