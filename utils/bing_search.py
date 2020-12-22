import asyncio

import re
from collections import AsyncIterable
from re import Match
from typing import AnyStr, Optional
from urllib.parse import quote_plus

import aiohttp

_BASE_URL = 'https://www.bing.com'


async def search(query, session: aiohttp.ClientSession, delay=1):
    url = _BASE_URL + f'/search?q={quote_plus(query)}'
    async for page in result_pages(session, url):
        for match in re.finditer(r'<h2>.+?href="(.+?)"', page):
            yield match.group(1)
        await asyncio.sleep(delay)


async def result_pages(session: aiohttp.ClientSession, url: str):
    while True:
        async with session.get(url) as resp:
            page = await resp.text()
        yield page
        # Next page of search results
        next_url_match = re.search(r'title="Next page" href="(.+?)"', page)
        if not next_url_match:
            return
        url = next_url_match.group(1)


async def first_match(regex: AnyStr, strings: AsyncIterable) -> Optional[Match]:
    async for result in strings:
        match = re.match(regex, result)
        if match:
            return match
