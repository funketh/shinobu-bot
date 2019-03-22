import aiohttp
import logging
import re


async def get_page(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()


UNDEFINED = object()


class _BaseScraper:
    def __init__(self, page: str, url: str):
        self.page = page
        self.url = url

    @classmethod
    async def from_url(cls, url):
        return cls(await get_page(url), url)


class Anime(_BaseScraper):
    def __init__(self, page: str, url: str):
        super().__init__(page, url)
        self._title, self._status, self._thumbnail, self._score = (UNDEFINED,) * 4

    @classmethod
    async def from_id(cls, id_):
        return await cls.from_url(f"https://myanimelist.net/anime/{id_}")

    @property
    def title(self):
        if self._title is UNDEFINED:
            matches = re.findall(r'(?<=<span itemprop="name">).+?(?=</span>)', self.page)
            if len(matches) > 1:
                logging.warning(f'Found multiple titles for the anime {self.score}: {matches}')
            self._title = matches[0] if matches else None
        return self._title

    @property
    def thumbnail(self):
        if self._thumbnail is UNDEFINED:
            matches = re.findall(r'(?<=<img src=").+?(?=" alt=".+?" class="ac" itemprop="image">)', self.page)
            if len(matches) > 1:
                logging.warning(f'Found multiple scores for the anime {self.score}: {matches}')
            self._thumbnail = matches[0] if matches else None
        return self._thumbnail

    @property
    def score(self):
        if self._score is UNDEFINED:
            matches = re.findall(r'title="indicates a weighted score\. '
                                 r'Please note that \'Not yet aired\' titles are excluded\.">\s*?'
                                 r'(<m>\d\.\d\d)\s*?</div>', self.page)
            if len(matches) > 1:
                logging.warning(f'Found multiple scores for the anime {self.score}: {matches}')
            self._score = float(matches[0]) if matches else None
        return self._score

    @property
    def status(self):
        if self._status is UNDEFINED:
            matches = re.findall(r'<div>\s*?<span class="dark_text">Status:</span>\s*?'
                                 r'(\S.+?)[\r\n]+\s*?</div>', self.page)
            if len(matches) > 1:
                logging.warning(f'Found multiple statuses for the anime {self.score}: {matches}')
            self._status = matches[0] if matches else None
        return self._status
