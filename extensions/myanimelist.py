import aiohttp
import discord
from discord.ext import commands
from typing import Optional, Dict

from utils.bing_search import search, first_match
from utils.myanimelist_scraper import Anime
from shinobu import Shinobu


async def search_first_mal_id(domain_appendix: str, query: str) -> Optional[int]:
    async with aiohttp.ClientSession() as session:
        search_results = search(f'site:myanimelist.net/{domain_appendix} {query}', session)
        match = await first_match(rf'https://myanimelist\.net/{domain_appendix}/(\d+)/[^/]+', search_results)
    if match is not None:
        return int(match.group(1))


async def remove_empty_fields(data: Dict):
    return await remove_empty_items(data.get('fields'))


async def remove_empty_items(data: Dict):
    for key, value in data.items():
        if key in ('', None) or value in ('', None):
            del data[key]


async def fixed_embed_from_data(data: Dict) -> discord.Embed:
    if not data.get('type'):
        data['type'] = 'rich'
    if isinstance(data.get('color'), discord.Color):
        data['color'] = data['color'].value
    return discord.Embed.from_data(data)


async def safe_embed_from_data(data: Dict) -> discord.Embed:
    await remove_empty_items(data)
    await remove_empty_fields(data)
    return await fixed_embed_from_data(data)


@commands.cooldown(1, 5, commands.BucketType.user)
@commands.command(aliases=['a'])
async def anime(ctx: commands.Context, *search_terms: str):
    """Gets information about an anime using myanimelist.net."""
    if len(search_terms) == 0:
        return await ctx.send('Please specify a search query.')

    series_id = await search_first_mal_id('anime', ' '.join(search_terms))
    if series_id is None:
        return await ctx.send("I couldn't find any results.")

    embed_msg = await ctx.send("*Getting the information from MyAnimeList.net...*")
    score_msg = await ctx.send("*Loading scores...*")
    ctx.typing()

    scraper = await Anime.from_id(series_id)

    embed = await safe_embed_from_data({
        'color': discord.Color.dark_blue(),
        'author': {
            'name': scraper.title,
            # 'url': None,
            # 'thumbnail': None,
        },
        'thumbnail': scraper.thumbnail,
        'fields': [
            {
                'name': 'score',
                'value': str(scraper.score),
            },
            {
                'name': 'status',
                'value': scraper.status,
            },
        ],
    })
    # Setting up the embed with all the dictionary values
    # embed = discord.Embed(colour=discord.Colour.dark_blue())
    # embed.set_author(name=scraper.title,
    #                  # url=scraper.url,
    #                  # icon_url=MAL_ICON
    #                  )
    # if scraper.thumbnail is not None:
    #     embed.set_thumbnail(url=scraper.thumbnail)
    # if scraper.score is not None:
    #     embed.add_field(name="Score", value=f"{scraper.score}")
    # if scraper.status is not None:
    #     embed.add_field(name="Status", value=f"{scraper.status}")

    # embed.add_field(name="Episodes", value=f"{scraper.get('episodes')}  ({scraper.get('duration')})")
    # studios = ', '.join([s['name'] for s in scraper['studios']])
    # embed.add_field(name="Source / Studios", value=f"{scraper.get('source')} / {studios}")
    # genres = ', '.join([g['name'] for g in scraper['genres']])
    # embed.add_field(name="Genres", value=genres)

    await embed_msg.edit(content=" ", embed=embed)

    # Getting the rating, status, etc. from favorite users
    # user_entries = await self.get_fav_users_stats(FAVORITES_FILE, scraper['mal_id'], "anime")
    # if user_entries != {}:
    #     translate_status = {
    #         1: "Watching",
    #         2: "Completed",
    #         3: "On-Hold",
    #         4: "Dropped",
    #         6: "Plan to Watch",
    #     }
    #     rows = []
    #     for username, entry in user_entries.items():
    #         user = await self.jikan.user(username)
    #         fav_star = '★' if self.has_as_fav(user, scraper['mal_id'], 'anime') else ''
    #         rows.append([
    #             username,
    #             translate_status[entry['watching_status']],
    #             str(entry['score']) + fav_star,
    #             f"{str(entry['watched_episodes'])}"
    #             f"/{str(entry['total_episodes'])}"
    #         ])
    #     stats_table = tabulate(
    #         rows,
    #         ["Username", "Status", "Score", "Eps."],
    #         tablefmt='grid'
    #     )
    #     await self.bot.edit_message(score_msg, new_content="`\n" + stats_table + "\n`")
    # else:
    #     await self.bot.delete_message(score_msg)


def setup(bot: Shinobu):
    cmds = (anime,)
    for cmd in cmds:
        bot.add_command(cmd)
