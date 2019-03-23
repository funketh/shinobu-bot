import asyncio

import re
from typing import AnyStr, AsyncIterable, Optional
from typing.re import Match
from urllib.parse import quote_plus

import aiohttp
from bs4 import BeautifulSoup

_BASE_URL = 'https://www.bing.com'


async def search(query, session: aiohttp.ClientSession, delay=0.5):
    url = _BASE_URL + f'/search?q={quote_plus(query)}'
    async for page in result_pages(session, url):
        for result in page.find(id='b_results').find_all(class_='b_algo'):
            yield result.find('a')['href']
        await asyncio.sleep(delay)


async def result_pages(session: aiohttp.ClientSession, url):
    while True:
        async with session.get(url) as resp:
            page = BeautifulSoup(await resp.text(), 'html.parser')
        if page.find(id='b_results'):
            yield page
        # Next page of search results
        try:
            url = _BASE_URL + page.find(class_='sb_pagN sb_pagN_bp b_widePag sb_bp ')['href']
        except TypeError:
            return


async def first_match(regex: AnyStr, strings: AsyncIterable) -> Optional[Match]:
    async for result in strings:
        match = re.match(regex, result)
        if match:
            return match
