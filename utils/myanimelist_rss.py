import re
from typing import Tuple, Generator

import feedparser

from utils import myanimelist_scraper
from utils.database import DB


def new_mal_content(db: DB, content_type: str, user_id: int, mal_username: str)\
        -> Generator[Tuple[int, int, int], None, None]:
    d = feedparser.parse(
        f"https://myanimelist.net/rss.php?type="
        f"{(content_type == 'anime' and 'rwe') or (content_type == 'manga' and 'rrm')}"
        f"&u={mal_username}"
    )
    already_rewarded = dict(db.execute(
        r'SELECT id, amount FROM consumed_media WHERE type=? AND user=?',
        [content_type, user_id]
    ).fetchall())
    for item in d.entries:
        series_id = int(re.match(rf'https://myanimelist\.net/{content_type}/(\d+)/.*', item.link).group(1))
        consumed_amount = int(re.match(r'.* - (\d+) of .* episodes', item.description).group(1))
        old_amount = already_rewarded.get(series_id, 0)
        if old_amount < consumed_amount:
            yield series_id, old_amount, consumed_amount


async def calculate_reward(content_type: str, series_id: int, amount: int) -> int:
    if content_type == 'anime':
        a = await myanimelist_scraper.Anime.from_id(series_id)
        duration = a.duration.seconds
    else:
        raise ValueError(f'unsupported content_type: {content_type}')
    return (((duration * amount) // 60) // 5) * 1
