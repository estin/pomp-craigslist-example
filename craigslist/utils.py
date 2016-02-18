import os
import socket
import datetime

import msgpack
from aiomeasures import StatsD


HOSTNAME = socket.gethostname()
METRIC_ITEMS_PARSED_KEY = 'crawler.%s.items.parsed' % HOSTNAME
METRIC_ITEMS_IMPORTED_KEY = 'crawler.%s.items.imported' % HOSTNAME

METRIC_REQUESTS_STARTED_KEY = 'crawler.%s.requests.started' % HOSTNAME
METRIC_REQUESTS_FINISHED_KEY = 'crawler.%s.requests.finished' % HOSTNAME
METRIC_EXCEPTIONS_KEY = 'crawler.%s.exceptions' % HOSTNAME

METRIC_QUEUE_SIZE_KEY = 'crawler.queue.size'


def get_redis_endpoint():
    return (
        os.environ.get('REDIS_PORT_6379_TCP_ADDR'),
        os.environ.get('REDIS_PORT_6379_TCP_PORT'),
    )


def get_kafka_endpoints():
    return [
        '%s:%s' % (
            os.environ.get('KAFKA_%i_PORT_9092_TCP_ADDR' % i),
            os.environ.get('KAFKA_%i_PORT_9092_TCP_PORT' % i),
        ) for i in range(1, 10)
        if 'KAFKA_%i_PORT_9092_TCP_ADDR' % i in os.environ
    ]


def get_statsd_client(sync=False):
    return (StatsD if not sync else SyncStatsD)(
        'udp://%s:%s' % (
            os.environ.get('GRAFANA_PORT_8125_UDP_ADDR'),
            os.environ.get('GRAFANA_PORT_8125_UDP_PORT'),
        )
    )


class MsgPackSerializer(object):

    def _decode(self, obj):
        if b'__datetime__' in obj:
            obj = datetime.datetime.strptime(
                obj[b'as_str'].decode(), "%Y%m%dT%H:%M:%S.%f"
            )
        return obj

    def _encode(self, obj):
        if isinstance(obj, datetime.datetime):
            return {
                '__datetime__': True,
                'as_str': obj.strftime("%Y%m%dT%H:%M:%S.%f")
            }
        return obj

    def dumps(self, data):
        return msgpack.packb(data, default=self._encode)

    def loads(self, data):
        return msgpack.unpackb(data, object_hook=self._decode)


class SyncStatsD(StatsD):

    def register(self, metric):
        self.collector.append(metric)
        self.loop.run_until_complete(self.send())
        return metric
