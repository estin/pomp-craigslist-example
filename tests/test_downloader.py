import asyncio
from pomp.core.utils import Planned

from craigslist.downloader import (
    AiohttpRequest, AiohttpResponse, AiohttpDownloader,
)

from utils import asyncio_test


@asyncio_test
def test_downloader(loop=None):
    future = asyncio.Future()
    downloader = AiohttpDownloader()
    request = AiohttpRequest('https://python.org')

    result = list(downloader.get((request, )))[0]
    assert isinstance(result, Planned)

    def check(data):
        response = data.result()
        assert isinstance(response, AiohttpResponse)
        assert request == response.request
        assert response.body
        future.set_result(None)

    result.add_done_callback(check)

    return future
