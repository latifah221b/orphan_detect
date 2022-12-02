import asyncio
from urllib.parse import urlparse
from Urlspinging.urlsStatus import http_normalize_slashes
import re
import aiohttp

from aiohttp.client import ClientSession
def addhttps(url:str):
    if not re.match('(?:http|ftp|https)://', url):
        url = 'https://{}'.format(url)
    return url

async def download_link(url:str,session:ClientSession,available_links:list, json_ele):
    url = addhttps(url)
    url = url.replace("\n", "")

    async with session.get(url) as response:
        result = await response.text()
        if response.status == 200:
            if url == http_normalize_slashes(str(response.url)):
                available_links.append(json_ele)
        else:
           print("hi")


async def download_all(urls:list):
    my_conn = aiohttp.TCPConnector(limit=10)
    async with aiohttp.ClientSession(connector=my_conn) as session:
        tasks = []
        available_links = []
        for url in urls:

            task = asyncio.ensure_future(download_link(url=url["url"],session=session,
                                                       available_links=available_links,json_ele= url))
            tasks.append(task)
        await asyncio.gather(*tasks,return_exceptions=True)
        return available_links



