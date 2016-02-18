import logging
from pomp.core.base import BaseMiddleware

from craigslist.utils import (
    get_statsd_client, METRIC_REQUESTS_STARTED_KEY,
    METRIC_REQUESTS_FINISHED_KEY, METRIC_EXCEPTIONS_KEY,
)


exceptions_log = logging.getLogger('exceptions')


class LogExceptionMiddleware(BaseMiddleware):
    def process_exception(self, exception, crawler, downloader):
        # re-raise and log it to separate logger
        try:
            raise exception.exception
        except Exception:
            exceptions_log.exception('On request: %s', exception.request)
        return exception


class MetricsMiddleware(BaseMiddleware):

    def __init__(self):
        self.statsd = get_statsd_client()

    def process_request(self, request, crawler, downloader):
        self.statsd.incr(METRIC_REQUESTS_STARTED_KEY)
        return request

    def process_response(self, response, crawler, downloader):
        self.statsd.incr(METRIC_REQUESTS_FINISHED_KEY)
        return response

    def process_exception(self, exception, crawler, downloader):
        self.statsd.incr(METRIC_EXCEPTIONS_KEY)
        return exception
