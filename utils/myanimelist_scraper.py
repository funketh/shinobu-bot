import aiohttp
import logging
import re

async def get_page(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()

def lazy_property(func):
    attr_name = '_lazy_' + func.__name__

    @property
    def _lazy_property(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, func(self))
        return getattr(self, attr_name)

    return _lazy_property

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
            logging.warning(f'Found multiple titles for the anime {self.score}: {matches}')
        return matches[0].group(1) if matches else None

    @lazy_property
    def thumbnail(self) -> str:
        matches = list(re.finditer(r'<img src="(.+?)".*?itemprop="image">', self.page))
        if len(matches) > 1:
            logging.warning(f'Found multiple scores for the anime {self.score}: {matches}')
        return matches[0].group(1) if matches else None

    @lazy_property
    def score(self) -> float:
        matches = list(re.finditer(r'data-title=.score..*?\n\s*(\d\.\d\d)', self.page))
        if len(matches) > 1:
            logging.warning(f'Found multiple scores for the anime {self.score}: {matches}')
        return float(matches[0].group(1)) if matches else None

    @lazy_property
    def status(self) -> str:
        matches = list(re.finditer(r'<span.*?>Status:</span>\s*(.+?)\s\s', self.page))
        if len(matches) > 1:
            logging.warning(f'Found multiple statuses for the anime {self.score}: {matches}')
        return matches[0].group(1) if matches else None
