import asyncio
import aiohttp
from aiohttp.client import ClientSession

async def download_link(url:str,session:ClientSession,available_links:list):
    async with session.get(url) as response:
        result = await response.text()
        if response.status == 200:
            available_links.append(url)

async def download_all(urls:list):
    my_conn = aiohttp.TCPConnector(limit=10)
    async with aiohttp.ClientSession(connector=my_conn) as session:
        tasks = []
        available_links = []
        for url in urls:
            task = asyncio.ensure_future(download_link(url=url,session=session,
                                                       available_links=available_links))
            tasks.append(task)
        await asyncio.gather(*tasks,return_exceptions=True)
        return available_links






def http_normalize_slashes(url):
    url = str(url)
    segments = url.split('/')
    correct_segments = []
    for segment in segments:
        if segment != '':
            correct_segments.append(segment)
    first_segment = str(correct_segments[0])
    if first_segment.find('http') == -1:
        correct_segments = ['http:'] + correct_segments
    correct_segments[0] = correct_segments[0] + '/'
    normalized_url = '/'.join(correct_segments)
    return normalized_url