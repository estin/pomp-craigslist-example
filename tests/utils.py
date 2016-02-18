import os
import logging
import asyncio

from craigslist.downloader import AiohttpRequest, AiohttpResponse

here = os.path.dirname(__file__)

logging.basicConfig(level=logging.DEBUG)


def asyncio_test(f):
    def wrapper(*args, **kwargs):
        coro = asyncio.coroutine(f)
        loop = asyncio.get_event_loop()
        kwargs['loop'] = loop
        future = coro(*args, **kwargs)
        loop.run_until_complete(future)
    return wrapper


def mock_response(filepath, request_instance=None, response_class=None):
    request_instance = request_instance or AiohttpRequest(url="mocked")
    response_class = response_class or AiohttpResponse
    with open(os.path.join(here, filepath), 'r') as f:
        response = response_class(
            request=request_instance,
            body=f.read()
        )
    return response
