import asyncio
import uuid
from io import StringIO

from craigslist.pipeline import KafkaPipeline, MetricsPipeline
from craigslist.item import CraigsListItem

from utils import asyncio_test


def test_kafka_pipeline():
    item = CraigsListItem(
        url='http://test.com/',
        city_code='chicago',
        title='kid bike',
        price='10',
        description='nice',
    )

    # send item to kafka
    pipeline = KafkaPipeline()
    pipeline.TOPIC = 'test_topic_%s' % uuid.uuid4().hex
    pipeline.start(None)
    pipeline.process(None, item)
    pipeline.stop(None)

    # dump item as csv from kafka
    csv_file = StringIO()
    pipeline.dump_to_csv(
        csv_file,
        topic=pipeline.TOPIC,
        timeout=1000,  # wait 0.5s for new data
    )
    assert item.url in csv_file.getvalue()


@asyncio_test
def test_metrics_pipeine(loop=None):
    item = CraigsListItem(
        url='http://test.com/',
        city_code='chicago',
        title='kid bike',
        price='10',
        description='nice',
        session_id='test_session',
    )
    metrics = MetricsPipeline()
    metrics.start(None)
    metrics.process(None, item)
    yield from asyncio.sleep(.1)
    metrics.close(None)
