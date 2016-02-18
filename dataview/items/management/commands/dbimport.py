import logging

from django.db import transaction
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError

from dataview.items.models import CraigsListItem
from craigslist.pipeline import KafkaPipeline
from craigslist.utils import get_statsd_client, METRIC_ITEMS_IMPORTED_KEY


log = logging.getLogger('dataview.dbimport')


class Command(BaseCommand):
    help = 'import data from kafka to db'

    def handle(self, *args, **options):
        try:
            self._handle(*args, **options)
        except Exception:
            log.exception("Exception")

    def _handle(self, *args, **options):

        statsd = get_statsd_client(sync=True)

        def _items_factory(items):
            for item in items:
                instance = CraigsListItem(**dict(
                    # convert dict byte keys to string keys and use it as
                    # keywords
                    (k.decode(), v) for k, v in item.items()
                ))

                # validate data before insert
                try:
                    instance.full_clean()
                except ValidationError as e:
                    log.debug('Invalid data(%s): %s', e, dict(item))
                else:
                    yield instance

        @transaction.atomic()
        def do_bulk_insert(items):
            cleaned_items = list(_items_factory(items))
            if cleaned_items:
                CraigsListItem.objects.bulk_create(cleaned_items)
            return cleaned_items

        log.debug(
            'Start import data from kafka',
        )

        for items in KafkaPipeline.dump_data(
                timeout=500, poll_timeout=5000, enable_auto_commit=True):

            if items:
                imported = do_bulk_insert(items)
                log.debug(
                    'Successfully imported %s from %s',
                    len(imported), len(items),
                )

                statsd.incr(METRIC_ITEMS_IMPORTED_KEY, value=len(imported))
