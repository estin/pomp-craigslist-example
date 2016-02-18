import logging
import pickle
import asyncio

from pomp.core.base import BaseQueue
from pomp.core.utils import iterator


log = logging.getLogger(__name__)


# add to queue only unique requests
add_new_request_lua_template = """
if redis.call('sadd', '{set_key}', ARGV[1]) == 1 then
    return redis.call('rpush', '{queue_key}', ARGV[2]);
else
    return nil;
end
"""


class RedisQueue(BaseQueue):
    set_key = 'all'
    queue_key = 'queue'
    serializer = pickle

    def __init__(self, redis):
        self.redis = redis
        self.script_sha = None

    @asyncio.coroutine
    def register_script(self):
        self.script_sha = yield from self.redis.script_load(
            add_new_request_lua_template.format(
                set_key=self.set_key,
                queue_key=self.queue_key,
            )
        )

    @asyncio.coroutine
    def get_requests(self):
        _, result = yield from self.redis.blpop(self.queue_key)
        requests = self.serializer.loads(result)
        log.debug("From queue: %s", requests)
        return requests

    @asyncio.coroutine
    def put_requests(self, requests):
        if not self.script_sha:
            yield from self.register_script()

        for item in iterator(requests):
            log.debug("Put to queue: %s", item)
            data = self.serializer.dumps(item)
            yield from self.redis.evalsha(
                self.script_sha, keys=[], args=[item.get_identity(), data, ],
            )

    @asyncio.coroutine
    def qsize(self):
        size = yield from self.redis.llen(self.queue_key)
        log.debug("queue size: %s", size)
        return size
