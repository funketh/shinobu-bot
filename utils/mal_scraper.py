from __future__ import annotations

import re
from datetime import timedelta
from typing import Optional, Union, Tuple

import aiohttp

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
    async def from_url(cls, url) -> _BaseScraper:
        return cls(await get_page(url), url)

    def safe_single_match(self, pattern, **kwargs) -> Union[str, Tuple[str, ...], None]:
        matches = re.findall(pattern, self.page, **kwargs)
        length = len(matches)
        if length == 1:
            return matches[0]
        if length > 1:
            raise ValueError(f"Found multiple matches for '{pattern}' on {self.url}: {matches}")


class AnimeMangaAgnosticScraper(_BaseScraper):
    @lazy_property
    def title(self) -> str:
        return self.safe_single_match(r'<span(?=.*itemprop="name").*>(.+?)</span>')

    @lazy_property
    def thumbnail(self) -> Optional[str]:
        return self.safe_single_match(rf'<img(?=.*alt="{self.title}").*src="(.+?)".*>')

    @lazy_property
    def score(self) -> Optional[float]:
        if match := self.safe_single_match(r'<div(?=.*class="score-label).*>(\d\.\d\d)</div>'):
            return float(match)

    @lazy_property
    def status(self) -> Optional[str]:
        return self.safe_single_match(r'<span.*?>Status:</span>\s*(.+?)\s*<')


class Anime(AnimeMangaAgnosticScraper):
    @classmethod
    async def from_id(cls, id_) -> Anime:
        return await cls.from_url(f"https://myanimelist.net/anime/{id_}")

    @lazy_property
    def duration(self) -> Optional[timedelta]:
        if match := self.safe_single_match(r'<span.*?>Duration:</span>\s*(?:(\d+) hr.)?\s*(?:(\d+) min.)?'):
            hours, minutes = match
            hours = int(hours) if hours else 0
            minutes = int(minutes) if minutes else 0
            return timedelta(hours=hours, minutes=minutes)


class Manga(AnimeMangaAgnosticScraper):
    @classmethod
    async def from_id(cls, id_) -> Manga:
        return await cls.from_url(f"https://myanimelist.net/manga/{id_}")

    @lazy_property
    def volumes(self) -> Optional[int]:
        match = self.safe_single_match(r'<span.*?>Volumes:</span>\s*(.+?)\s')
        if match and match != 'Unknown':
            return int(match)

    @lazy_property
    def chapters(self) -> Optional[int]:
        match = self.safe_single_match(r'<span.*?>Chapters:</span>\s*(.+?)\s')
        if match and match != 'Unknown':
            return int(match)
