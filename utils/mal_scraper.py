from __future__ import annotations

import re
from abc import abstractmethod
from datetime import timedelta
from typing import Optional, Union, Tuple, Protocol, ClassVar, TypeVar, Iterable, Pattern

import aiohttp
import discord
from async_property import async_cached_property


class BaseScraper:
    def __init__(self, url: str):
        self.url = url

    @async_cached_property
    async def page(self) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url) as response:
                return await response.text()

    async def _safe_single_match(self, pattern, **kwargs) -> Union[str, Tuple[str, ...], None]:
        matches = re.findall(pattern, await self.page, **kwargs)
        length = len(matches)
        if length == 1:
            return matches[0]
        if length > 1:
            raise ValueError(f"Found multiple matches for '{pattern}' on {self.url}: {matches}")


_ContentT = TypeVar('_ContentT', bound='Content')


class Content(Protocol):
    domain_suffix: ClassVar[str]
    rss_types: ClassVar[Iterable[str]]
    consumed_regex: ClassVar[Pattern]

    @classmethod
    @abstractmethod
    def from_id(cls, id_: int) -> _ContentT: raise NotImplementedError

    @abstractmethod
    async def to_embed(self) -> discord.Embed: raise NotImplementedError

    @abstractmethod
    async def calculate_reward(self, amount: int) -> int: raise NotImplementedError


class _AnimeMangaAgnosticScraper(BaseScraper):
    async def to_embed(self) -> discord.Embed:
        embed = discord.Embed()
        embed.colour = discord.Colour.dark_blue()
        embed.set_author(name=await self.title, url=self.url)
        if await self.thumbnail:
            embed.set_thumbnail(url=self.thumbnail)
        if await self.score:
            embed.add_field(name='Score', value=self.score)
        if await self.status:
            embed.add_field(name='Status', value=self.status)
        return embed

    @async_cached_property
    async def title(self) -> str:
        return await self._safe_single_match(r'<span(?=.*itemprop="name").*>(.+?)</span>')

    @async_cached_property
    async def thumbnail(self) -> Optional[str]:
        return await self._safe_single_match(rf'<img(?=.*alt="{self.title}").*src="(.+?)".*>')

    @async_cached_property
    async def score(self) -> Optional[float]:
        if match := await self._safe_single_match(r'<div(?=.*class="score-label).*>(\d\.\d\d)</div>'):
            return float(match)

    @async_cached_property
    async def status(self) -> Optional[str]:
        return await self._safe_single_match(r'<span.*?>Status:</span>\s*(.+?)\s*<')


class Anime(_AnimeMangaAgnosticScraper, Content):
    domain_suffix = 'anime'
    rss_types = {'rwe', 'rw'}
    consumed_regex = re.compile(r'.*- (\d+) of .* episodes')

    @classmethod
    def from_id(cls, id_) -> Anime:
        return cls(f"https://myanimelist.net/anime/{id_}")

    async def calculate_reward(self, amount: int) -> int:
        return ((await self.duration).seconds * amount) // 300

    @async_cached_property
    async def duration(self) -> Optional[timedelta]:
        if match := await self._safe_single_match(r'<span.*?>Duration:</span>\s*(?:(\d+) hr.)?\s*(?:(\d+) min.)?'):
            hours, minutes = match
            hours = int(hours) if hours else 0
            minutes = int(minutes) if minutes else 0
            return timedelta(hours=hours, minutes=minutes)


class Manga(_AnimeMangaAgnosticScraper, Content):
    domain_suffix = 'manga'
    rss_types = {'rrm', 'rm'}
    consumed_regex = re.compile(r'.*- (\d+) of .* chapters')

    async def to_embed(self) -> discord.Embed:
        embed = await super().to_embed()
        if await self.volumes:
            embed.add_field(name='Volumes', value=self.volumes)
        if await self.chapters:
            embed.add_field(name='Chapters', value=self.chapters)
        return embed

    @classmethod
    def from_id(cls, id_) -> Manga:
        return cls(f"https://myanimelist.net/manga/{id_}")

    async def calculate_reward(self, amount: int) -> int:
        # 5 minutes are rewarded for each chapter.
        # For reference, myanimelist.net uses (chapter = 8 min) and (volume = 72 min).
        # TODO: one could make this depend on whether the series is a manga or a novel
        return amount

    @async_cached_property
    async def volumes(self) -> Optional[int]:
        match = await self._safe_single_match(r'<span.*?>Volumes:</span>\s*(.+?)\s')
        if match and match != 'Unknown':
            return int(match)

    @async_cached_property
    async def chapters(self) -> Optional[int]:
        match = await self._safe_single_match(r'<span.*?>Chapters:</span>\s*(.+?)\s')
        if match and match != 'Unknown':
            return int(match)
