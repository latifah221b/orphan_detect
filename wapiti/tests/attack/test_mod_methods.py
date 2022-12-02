from asyncio import Event
from unittest.mock import AsyncMock

import httpx
import respx
import pytest

from wapitiCore.net.classes import CrawlerConfiguration
from wapitiCore.net import Request, Response
from wapitiCore.net.crawler import AsyncCrawler
from wapitiCore.attack.mod_methods import ModuleMethods


@pytest.mark.asyncio
@respx.mock
async def test_whole_stuff():
    # Test attacking all kind of parameter without crashing
    respx.options("http://perdu.com/").mock(
        return_value=httpx.Response(200, text="Default page", headers={"Allow": "GET,POST,HEAD"})
    )

    respx.options("http://perdu.com/dav/").mock(
        return_value=httpx.Response(200, text="Private section", headers={"Allow": "GET,POST,HEAD,PUT"})
    )

    persister = AsyncMock()
    all_requests = []

    request = Request("http://perdu.com/")
    request.path_id = 1
    response = Response(
        httpx.Response(status_code=200),
        url="http://perdu.com/"
    )
    all_requests.append((request, response))

    request = Request("http://perdu.com/dav/")
    request.path_id = 2
    response = Response(
        httpx.Response(status_code=200),
        url="http://perdu.com/dav/"
    )
    all_requests.append((request, response))

    crawler_configuration = CrawlerConfiguration(Request("http://perdu.com/"), timeout=1)
    async with AsyncCrawler.with_configuration(crawler_configuration) as crawler:
        options = {"timeout": 10, "level": 2}

        module = ModuleMethods(crawler, persister, options, Event(), crawler_configuration)
        module.do_get = True
        for request, response in all_requests:
            await module.attack(request, response)

        assert persister.add_payload.call_count == 1
        assert "http://perdu.com/dav/" in persister.add_payload.call_args_list[0][1]["info"]
