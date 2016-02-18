import time
import logging

from kafka import KafkaConsumer, KafkaProducer

from pomp.core.base import BasePipeline
from pomp.contrib.pipelines import CsvPipeline

from craigslist.item import CraigsListItem
from craigslist.utils import (
    get_kafka_endpoints, get_statsd_client, MsgPackSerializer,
    METRIC_ITEMS_PARSED_KEY,
)


log = logging.getLogger(__name__)


class ItemLogPipeline(BasePipeline):

    def process(self, crawler, item):
        log.debug('ITEM: %s', dict(item))
        return item


class MetricsPipeline(BasePipeline):

    def start(self, crawler):
        self.statsd = get_statsd_client()

    def process(self, crawler, item):
        self.statsd.incr(METRIC_ITEMS_PARSED_KEY)
        return item

    def close(self, crawler):
        self.statsd.close()


class KafkaPipeline(BasePipeline):
    TOPIC = 'craigslist'
    SERIALIZER = MsgPackSerializer()

    def start(self, crawler):

        # TODO: remove this hack
        # HACK
        log.debug("Wait 5s to allow kafka node to be ready")
        time.sleep(5)

        endpoints = list(get_kafka_endpoints())
        log.debug("Connect to kafka as producer - %s", endpoints)
        if not endpoints:
            raise RuntimeError("Kafka endpoints not defined")
        self.producer = KafkaProducer(bootstrap_servers=endpoints)

    def process(self, crawler, item):
        self.producer.send(
            self.TOPIC,
            self.SERIALIZER.dumps(item),
        )
        return item

    def stop(self, crawler):
        self.producer.flush()
        self.producer.close()

    @classmethod
    def dump_data(
            cls, topic=None, timeout=None, poll_timeout=None,
            enable_auto_commit=False):

        # TODO: remove this hack
        # HACK
        log.debug("Wait 5s to allow kafka node to be ready")
        time.sleep(5)

        topic = topic or cls.TOPIC
        endpoints = list(get_kafka_endpoints())
        log.debug("Connect to kafka as consumer - %s", endpoints)
        if not endpoints:
            raise RuntimeError("Kafka endpoints not defined")

        consumer = KafkaConsumer(
            topic,
            auto_offset_reset='earliest',
            enable_auto_commit=enable_auto_commit,
            value_deserializer=cls.SERIALIZER.loads,
            bootstrap_servers=endpoints,
            consumer_timeout_ms=timeout or -1,
        )

        # TODO use native kafka-python poll
        if poll_timeout:
            while True:
                yield list(data.value for data in consumer)
                time.sleep(poll_timeout / 1000.0)
        else:
            for data in consumer:
                yield data.value

        consumer.close()

    @classmethod
    def dump_to_csv(cls, to_file, topic=None, timeout=None):
        log.debug("Dump topic <%s> to %s", topic, to_file)

        csv_pipeline = CsvPipeline(to_file)
        csv_pipeline.start(None)

        for item in cls.dump_data(topic, timeout):
            # we must reinitialize item to restore fields and values ordering
            csv_pipeline.process(
                None,
                CraigsListItem(**dict(
                    # convert dict byte keys to string keys and use it as
                    # keywords
                    (k.decode(), v) for k, v in item.items()
                ))
            )

        csv_pipeline.stop(None)
