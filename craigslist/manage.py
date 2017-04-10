import sys
import signal
import functools
import urllib.parse
from collections import defaultdict

import asyncio
import argparse
import aioredis
import aiohttp

from pomp.contrib.asynciotools import AioPomp, AioConcurrentCrawler

from craigslist.log import LOGGING
from craigslist.utils import (
    get_redis_endpoint, get_statsd_client, METRIC_QUEUE_SIZE_KEY,
)
from craigslist.queue import RedisQueue
from craigslist.pipeline import (
    ItemLogPipeline, KafkaPipeline, MetricsPipeline,
)
from craigslist.crawler import CraigsListCrawler, ListRequest, ItemRequest
from craigslist.downloader import AiohttpDownloader, AiohttpResponse
from craigslist.middleware import LogExceptionMiddleware, MetricsMiddleware
from craigslist.item import CraigsListItem


@asyncio.coroutine
def get_redis(loop=None):
    endpoint = get_redis_endpoint()
    print('connect to redis on %s:%s' % endpoint)
    return (
        yield from aioredis.create_redis(endpoint, loop=loop)
    )


@asyncio.coroutine
def start_crawler(loop):
    redis = yield from get_redis(loop)
    queue = RedisQueue(redis)

    # TODO only one instance of the crawler must gather queue size
    # start gather queue size metrics
    statsd = get_statsd_client()

    @asyncio.coroutine
    def _publish_queue_size_metric():
        yield from asyncio.sleep(5.0)
        statsd.gauge(
            METRIC_QUEUE_SIZE_KEY,
            (yield from queue.qsize())
        )
        asyncio.Task(_publish_queue_size_metric(), loop=loop)
    asyncio.Task(_publish_queue_size_metric(), loop=loop)

    # configure engine
    pomp = AioPomp(
        downloader=AiohttpDownloader(
            max_concurent_request_count=3,
        ),
        queue=queue,
        middlewares=(
            LogExceptionMiddleware(),
            MetricsMiddleware(),
        ),
        pipelines=(
            ItemLogPipeline(),
            KafkaPipeline(),
            MetricsPipeline(),
        ),
    )

    # start
    yield from pomp.pump(AioConcurrentCrawler(
        worker_class=CraigsListCrawler,
        pool_size=2,
    ))
    redis.close()


@asyncio.coroutine
def start_session(loop, session_id, path):
    redis = yield from get_redis(loop)
    queue = RedisQueue(redis)
    url_tmpl = "https://{city_code}.craigslist.org/"
    yield from queue.put_requests([
        ListRequest(
            session_id=session_id,
            city_code=city_code,
            url=urllib.parse.urljoin(
                url_tmpl.format(city_code=city_code),
                path,
            ),
        ) for city_code in (
            'newyork',
            'sfbay',
            'chicago',
            # put here more cities
        )
    ])
    redis.close()


@asyncio.coroutine
def clear_queue(loop):
    redis = yield from get_redis(loop)
    yield from redis.flushall()
    redis.close()


@asyncio.coroutine
def check_xpath(loop, url):
    crawler = CraigsListCrawler()

    print('fetch and parse list request: %s...' % url)
    r = yield from aiohttp.get(url)
    body = yield from r.text()
    response = AiohttpResponse(
        request=ListRequest(
            url=url,
            session_id='xpath-check',
            city_code=urllib.parse.urlparse(url).netloc.split('.')[0],
        ),
        body=body,
    )
    result_by_type = defaultdict(list)
    for item in crawler.extract_items(response):
        result_by_type[type(item)].append(item)

    for _type, items in result_by_type.items():
        print('%s count: %s' % (_type.__name__, len(items)))

    item_requests = result_by_type[ItemRequest]
    if not item_requests:
        print('xpath: OUT OF DATE')
        return

    request = item_requests[0]

    print('\nfetch and parse item request %s...' % request.url)
    r = yield from aiohttp.get(request.url)
    body = yield from r.text()
    response = AiohttpResponse(
        request=request,
        body=body,
    )
    result_by_type = defaultdict(list)
    for item in crawler.extract_items(response):
        result_by_type[type(item)].append(item)

    for _type, items in result_by_type.items():
        print('%s count: %s' % (_type.__name__, len(items)))

    item = result_by_type[CraigsListItem][0]
    if not item:
        print('xpath: OUT OF DATE')
        return

    ItemLogPipeline().process(crawler, item)

    if not all((item.title, item.price, item.description)):
        print('xpath: OUT OF DATE')
        return

    print('\nxpath: ACTUAL')


def main():

    import logging.config
    logging.config.dictConfig(LOGGING)

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser('crawl')

    session_parser = subparsers.add_parser('session')
    session_parser.add_argument('session_id')
    session_parser.add_argument('path')

    subparsers.add_parser('clearqueue')

    check_xpath_parser = subparsers.add_parser('check-xpath')
    check_xpath_parser.add_argument('url')

    dataview_parser = subparsers.add_parser('dataview')
    dataview_parser.add_argument(
        "django_command", metavar="django_command", type=str, nargs='*',
    )

    args = parser.parse_args()

    if args.command == 'dataview':
        # dive in django management system
        from django.core.management import execute_from_command_line
        execute_from_command_line(sys.argv[1:])
    else:
        # asyncio other project stuff
        loop = asyncio.get_event_loop()

        def ask_exit(signame):
            print("got signal %s: exit" % signame)
            loop.stop()

        for signame in ('SIGINT', 'SIGTERM'):
            loop.add_signal_handler(
                getattr(signal, signame),
                functools.partial(ask_exit, signame)
            )

        task = None
        if args.command == 'crawl':
            task = start_crawler(loop)
        elif args.command == 'session':
            task = start_session(loop, args.session_id, args.path)
        elif args.command == 'clearqueue':
            task = clear_queue(loop)
        elif args.command == 'check-xpath':
            task = check_xpath(loop, args.url)

        if task:
            try:
                loop.run_until_complete(task)
            finally:
                loop.close()
