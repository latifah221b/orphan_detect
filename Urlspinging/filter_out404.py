import asyncio
import aiohttp
from aiohttp.client import ClientSession
def findDisabled(fullstring):
    blackword = "This app has been disabled"
    blackword1 = "404 Not Found"
    blackword2 = "403 Forbidden"
    if blackword in fullstring or blackword1 in fullstring or blackword2 in fullstring:
        return  False
    else:
        return True

async def filter_link(url:str,session:ClientSession,available_links:list):
    async with session.get(url) as response:
        result = await response.text()
        if findDisabled(result):
            available_links.append(url)


async def filter_all(urls:list):
    my_conn = aiohttp.TCPConnector(limit=10)
    async with aiohttp.ClientSession(connector=my_conn) as session:
        tasks = []
        available_links = []
        for url in urls:
            task = asyncio.ensure_future(filter_link(url=url,session=session,
                                                       available_links=available_links))
            tasks.append(task)
        await asyncio.gather(*tasks,return_exceptions=True)
        return available_links

