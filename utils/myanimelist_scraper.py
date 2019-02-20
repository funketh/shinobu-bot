import aiohttp
import re


async def get_page(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()


UNDEFINED = object()


class _BaseScraper:
    def __init__(self, page: str):
        self.page = page

    @classmethod
    async def from_url(cls, url):
        return cls(await get_page(url))


class Anime(_BaseScraper):
    def __init__(self, page: str):
        super().__init__(page)
        self._title, self._status, self._thumbnail, self._score = (UNDEFINED,) * 4

    @classmethod
    async def from_id(cls, id_):
        return await cls.from_url(f"http://myanimelist.net/anime/{id_}")

    @property
    def title(self):
        if self._title is UNDEFINED:
            self._title = re.search(r'(?<=<span itemprop="name">).+?(?=</span>)', self.page).group()
        return self._title

    @property
    def thumbnail(self):
        if self._thumbnail is UNDEFINED:
            match = re.search(r'(?<=<img src=").+?(?=" alt=".+?" class="ac" itemprop="image">)', self.page)
            self._thumbnail = match.group() if match else None
        return self._thumbnail

    @property
    def score(self):
        if self._score is UNDEFINED:
            match = re.search(r'title="indicates a weighted score\. '
                              r'Please note that \'Not yet aired\' titles are excluded\.">\s*?'
                              r'(?P<m>\d\.\d\d)\s*?</div>', self.page)
            self._score = float(match.group('m')) if match else None
        return self._score

    @property
    def status(self):
        if self._status is UNDEFINED:
            match = re.search(r'<div>\s*?<span class="dark_text">Status:</span>\s*?'
                              r'(?P<m>\S.+?)[\r\n]+\s*?</div>', self.page)
            self._status = match.group('m') if match else None
        return self._status


if __name__ == '__main__':
    import asyncio

    ani = asyncio.run(Anime.from_id(39265))
