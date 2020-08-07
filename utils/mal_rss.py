import re
from typing import Tuple, Iterator

import aiohttp
import feedparser

from utils.database import DB
from utils.mal_scraper import Anime


async def new_mal_content(db: DB, session: aiohttp.ClientSession, content_type: str, user_id: int, mal_username: str) \
        -> Iterator[Tuple[int, int, int]]:

    if content_type == 'anime':
        rss_types = {'rwe', 'rw'}
        consumed_regex = re.compile(r'.*- (\d+) of .* episodes')
    elif content_type == 'manga':
        rss_types = {'rrm', 'rm'}
        consumed_regex = re.compile(r'.*- (\d+) of .* chapters')
    else:
        raise ValueError(f'unsupported {content_type=}')

    entries = []
    for rss_type in rss_types:
        async with session.get(f"https://myanimelist.net/rss.php?type={rss_type}&u={mal_username}") as resp:
            feed = feedparser.parse(await resp.text())
            entries.extend(feed.entries)

    already_rewarded = dict(db.execute('SELECT id, amount FROM consumed_media WHERE type=? AND user=?',
                                       [content_type, user_id]))

    # only yield from inside the generator closure to avoid having to use an async generator
    def new_content_generator():
        for item in entries:
            series_id = int(re.match(rf'https://myanimelist\.net/{content_type}/(\d+)/.*', item.link).group(1))
            consumed_amount = int(consumed_regex.match(item.description).group(1))
            old_amount = already_rewarded.get(series_id, 0)
            if old_amount < consumed_amount:
                already_rewarded[series_id] = consumed_amount
                yield series_id, old_amount, consumed_amount

    return new_content_generator()


async def calculate_reward(content_type: str, series_id: int, amount: int) -> int:
    if content_type == 'anime':
        a = await Anime.from_id(series_id)
        duration = a.duration.seconds
    elif content_type == 'manga':
        # 5 minutes are rewarded for each chapter.
        # For reference, myanimelist.net uses (chapter = 8 min) and (volume = 72 min).
        # TODO: one could make this depend on whether the series is a manga or a novel
        duration = 300
    else:
        raise ValueError(f'unsupported {content_type=}')
    # 1 is rewarded per 5 minutes
    return (duration * amount) // 300
