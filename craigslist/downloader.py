import sys
import logging
import asyncio

import aiohttp

from pomp.core.base import (
    BaseHttpRequest, BaseHttpResponse, BaseDownloader,
)
from pomp.core.utils import Planned


log = logging.getLogger(__name__)


class AiohttpRequest(BaseHttpRequest):
    def __init__(self, url):
        self.url = url

    def __str__(self):
        return '<{s.__class__.__name__} url:{s.url}>'.format(s=self)


class AiohttpResponse(BaseHttpResponse):
    def __init__(self, request, body):
        self.req = request
        self.body = body

    @property
    def request(self):
        return self.req


class AiohttpDownloader(BaseDownloader):

    def __init__(self, *args, **kwargs):
        if 'max_concurent_request_count' in kwargs:
            self.max_concurent_request_count = kwargs.pop(
                'max_concurent_request_count'
            )
        else:
            self.max_concurent_request_count = 3
        super(AiohttpDownloader, self).__init__(*args, **kwargs)

    def get_workers_count(self):
        return self.max_concurent_request_count

    @asyncio.coroutine
    def _fetch(self, request, future):
        log.debug("[AiohttpDownloader] Start fetch: %s", request.url)
        r = yield from aiohttp.get(request.url)
        body = yield from r.text()
        log.debug(
            "[AiohttpDownloader] Done %s: size: %s", request.url, len(body),
        )
        future.set_result(AiohttpResponse(request, body))

    def get(self, requests):
        for request in requests:

            future = asyncio.Future()
            asyncio.ensure_future(self._fetch(request, future))

            planned = Planned()

            def build_response(f):
                planned.set_result(f.result())
            future.add_done_callback(build_response)

            yield planned
