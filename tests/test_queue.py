import aioredis

from craigslist.utils import get_redis_endpoint
from craigslist.queue import RedisQueue
from craigslist.crawler import ListRequest

from utils import asyncio_test


@asyncio_test
def test_queue(loop=None):

    endpoint = get_redis_endpoint()
    redis = yield from aioredis.create_redis(endpoint, loop=loop)

    yield from redis.flushall()

    queue = RedisQueue(redis)

    # put request to queue
    request = ListRequest(
        city_code='some_city',
        session_id='some_session',
        url='http://some.url',
    )
    yield from queue.put_requests(request)
    assert (yield from queue.qsize()) == 1

    # check queue size and get request from it
    result = yield from queue.get_requests()
    assert request.get_identity() == result.get_identity()
    assert (yield from queue.qsize()) == 0

    # put same request to queue again
    yield from queue.put_requests(request)
    assert (yield from queue.qsize()) == 0
