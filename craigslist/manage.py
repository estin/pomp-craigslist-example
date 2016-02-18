import sys
import signal
import functools
import urllib.parse

import asyncio
import argparse
import aioredis

from pomp.contrib.asynciotools import AioPomp, AioConcurrentCrawler

from craigslist.log import LOGGING
from craigslist.utils import (
    get_redis_endpoint, get_statsd_client, METRIC_QUEUE_SIZE_KEY,
)
from craigslist.queue import RedisQueue
from craigslist.pipeline import (
    ItemLogPipeline, KafkaPipeline, MetricsPipeline,
)
from craigslist.crawler import CraigsListCrawler, ListRequest
from craigslist.downloader import AiohttpDownloader
from craigslist.middleware import LogExceptionMiddleware, MetricsMiddleware


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

        if task:
            try:
                loop.run_until_complete(task)
            finally:
                loop.close()
