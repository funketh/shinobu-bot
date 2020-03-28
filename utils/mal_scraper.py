from datetime import timedelta

import aiohttp
import logging
import re

from utils.decorators import lazy_property


async def get_page(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()


class _BaseScraper:
    def __init__(self, page: str, url: str):
        self.page = page
        self.url = url

    @classmethod
    async def from_url(cls, url):
        return cls(await get_page(url), url)


class Anime(_BaseScraper):
    @classmethod
    async def from_id(cls, id_):
        return await cls.from_url(f"https://myanimelist.net/anime/{id_}")

    @lazy_property
    def title(self) -> str:
        matches = list(re.finditer(r'<h1.+?><span.+?>(.+?)</span>', self.page))
        if len(matches) > 1:
            logging.warning(f'Found multiple titles for the anime {self.url}: {matches}')
        return matches[0].group(1) if matches else None

    @lazy_property
    def thumbnail(self) -> str:
        matches = list(re.finditer(r'<img src="(.+?)".*?itemprop="image">', self.page))
        if len(matches) > 1:
            logging.warning(f'Found multiple scores for the anime {self.url}: {matches}')
        return matches[0].group(1) if matches else None

    @lazy_property
    def score(self) -> float:
        matches = list(re.finditer(r'data-title=.score..*?\n\s*(\d\.\d\d)', self.page))
        if len(matches) > 1:
            logging.warning(f'Found multiple scores for the anime {self.url}: {matches}')
        return float(matches[0].group(1)) if matches else None

    @lazy_property
    def status(self) -> str:
        matches = list(re.finditer(r'<span.*?>Status:</span>\s*(.+?)\s\s', self.page))
        if len(matches) > 1:
            logging.warning(f'Found multiple statuses for the anime {self.url}: {matches}')
        return matches[0].group(1) if matches else None

    @lazy_property
    def duration(self) -> timedelta:
        matches = list(re.finditer(r'<span.*?>Duration:</span>\s*(?:(\d+) hr.)?\s*(?:(\d+) min.)?', self.page))
        if len(matches) > 1:
            logging.warning(f'Found multiple durations for the anime {self.url}: {matches}')
        return timedelta(hours=int(matches[0].group(1) or 0), minutes=int(matches[0].group(2) or 0)) if matches else None
