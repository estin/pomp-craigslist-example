import re
import json
import hashlib
import logging
from urllib.parse import urljoin

from lxml import html

from pomp.core.base import BaseCrawler

from craigslist.item import CraigsListItem
from craigslist.downloader import AiohttpRequest


log = logging.getLogger(__name__)


class CraigsListRequestBase(AiohttpRequest):

    def __init__(self, *args, **kwargs):
        self.session_id = kwargs.pop('session_id')
        self.city_code = kwargs.pop('city_code')
        super(CraigsListRequestBase, self).__init__(*args, **kwargs)

    def get_identity(self):
        return hashlib.md5(
            b'|'.join(
                map(
                    lambda i: i if isinstance(i, bytes) else i.encode(),
                    (
                        self.session_id or '',
                        self.city_code or '',
                        self.url,
                    )
                )
            )
        ).hexdigest()

    def __str__(self):
        return '<{s.__class__.__name__} session_id:{s.session_id} ' \
            'url:{s.url}>'.format(s=self)


class ListRequest(CraigsListRequestBase):

    def __init__(self, *args, **kwargs):
        self.page_number = kwargs.pop('page_number', 0)
        super(ListRequest, self).__init__(*args, **kwargs)


class ItemRequest(CraigsListRequestBase):
    pass


class CraigsListCrawler(BaseCrawler):
    # limit number of parsed pages from paginator
    MAX_PAGE_NUMBER = 3

    URL_TEMPLATE = 'https://{city_code}.craigslist.org/'

    # list parse xpaths
    NEXT_PAGE_XPATH = "(//a[@title='next page']/@href)[1]"
    ITEMS_XPATH = '//li[@data-pid]'

    # item parse xpaths
    ITEM_TITLE = "(//title/text())[1]"
    ITEM_PRICE = "//span[@class='postingtitletext']" \
        "/span[@class='price']/text()"
    ITEM_DESCRIPTION = "//section[@id='postingbody']"

    ITEM_PHOTOS_RE = re.compile('var imgList\ =\ (.*)\;')

    def extract_items(self, response):
        tree = html.fromstring(response.body)

        if isinstance(response.request, ListRequest):
            yield from self._parse_list(response, tree)
        elif isinstance(response.request, ItemRequest):
            yield from self._parse_item(response, tree)
        else:
            raise RuntimeError(
                "Unknown request type: %s %s" % (
                    type(response.request), response.request,
                )
            )

    def _parse_list(self, response, tree):

        # yield next request for item parsing
        for item in tree.xpath(self.ITEMS_XPATH):
            link = ''.join(item.xpath('a/@href'))
            yield ItemRequest(
                session_id=response.request.session_id,

                # where
                city_code=response.request.city_code,

                # absolute url
                url=urljoin(
                    self.URL_TEMPLATE.format(
                        city_code=response.request.city_code
                    ),
                    link,
                )
            )

        # yield next request to parse next page
        if response.request.page_number < self.MAX_PAGE_NUMBER:

            next_page_link = tree.xpath(self.NEXT_PAGE_XPATH)
            log.debug("Next page link: %s", next_page_link)

            if next_page_link:
                yield ListRequest(
                    page_number=response.request.page_number + 1,
                    session_id=response.request.session_id,
                    city_code=response.request.city_code,

                    # absolute url
                    url=urljoin(
                        self.URL_TEMPLATE.format(
                            city_code=response.request.city_code
                        ),
                        next_page_link[0],
                    )
                )

    def _parse_item(self, response, tree):
        item = CraigsListItem()

        item.url = response.request.url
        item.session_id = response.request.session_id
        item.city_code = response.request.city_code

        item.title = tree.xpath(self.ITEM_TITLE)[0]

        # convert dollars to cents
        item.price = int(
            tree.xpath(self.ITEM_PRICE)[0].replace('$', '')
        ) * 100

        item.photos = [
            i['url'] for i in json.loads(
                self.ITEM_PHOTOS_RE.search(response.body).groups()[0]
            )
        ]
        item.description = tree.xpath(self.ITEM_DESCRIPTION)[0].text_content()

        yield item
