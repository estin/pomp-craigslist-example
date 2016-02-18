from craigslist.item import CraigsListItem
from craigslist.crawler import (
    ListRequest, ItemRequest, CraigsListCrawler
)

from utils import mock_response

crawler = CraigsListCrawler()


def test_crawler_list_parse():

    request = ListRequest(
        session_id='somesession',
        url='mocked',
        city_code='sfbay',
    )

    items = crawler.extract_items(
        mock_response(
            'data/list.html',
            request_instance=request,
        ),
    )

    next_list_requests = []

    for item in items:
        assert item.city_code == request.city_code
        assert item.session_id == request.session_id

        if isinstance(item, ListRequest):
            next_list_requests.append(item)
        else:
            assert isinstance(item, ItemRequest)

    assert len(next_list_requests) == 1
    assert next_list_requests[0].page_number == 1


def test_crawler_item_parse():

    request = ItemRequest(
        session_id='somesession',
        url='mocked',
        city_code='sfbay',
    )

    items = crawler.extract_items(
        mock_response(
            'data/item.html',
            request_instance=request,
        ),
    )

    for item in items:
        print('item:', dict(item))
        assert isinstance(item, CraigsListItem)
        assert item.url == request.url
        assert item.city_code == request.city_code
        assert item.title == 'kid bike'
