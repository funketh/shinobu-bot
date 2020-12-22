import re
from collections import Iterator

import aiohttp
import feedparser

from utils.database import DB
from utils.mal_scraper import Content


async def new_mal_content(db: DB, session: aiohttp.ClientSession, content_type: type[Content], user_id: int,
                          mal_username: str) -> Iterator[tuple[int, int, int]]:
    entries = []
    for rss_type in content_type.rss_types:
        async with session.get(f"https://myanimelist.net/rss.php?type={rss_type}&u={mal_username}") as resp:
            feed = feedparser.parse(await resp.text())
            entries.extend(feed.entries)

    already_rewarded = dict(db.execute('SELECT id, amount FROM consumed_media WHERE type=? AND user=?',
                                       [content_type.domain_suffix, user_id]))

    # only yield from inside the generator closure to avoid having to use an async generator
    def new_content_generator():
        for item in entries:
            series_match = re.match(rf'https://myanimelist\.net/{content_type.domain_suffix}/(\d+)/.*', item.link)
            series_id = int(series_match.group(1))
            consumed_match = content_type.consumed_regex.match(item.description)
            consumed_amount = int(consumed_match.group(1))
            old_amount = already_rewarded.get(series_id, 0)
            if old_amount < consumed_amount:
                already_rewarded[series_id] = consumed_amount
                yield series_id, old_amount, consumed_amount

    return new_content_generator()
