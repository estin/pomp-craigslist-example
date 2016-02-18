from datetime import datetime
from pomp.contrib.item import Item, Field


class CraigsListItem(Item):

    url = Field()
    city_code = Field()
    session_id = Field()

    title = Field()
    price = Field()
    photos = Field()
    description = Field()

    ts_created = Field()

    def __init__(self, *args, **kwargs):
        super(CraigsListItem, self).__init__(*args, **kwargs)

        if not self.ts_created:
            self.ts_created = datetime.now()

    def __str__(self):
        return 'city_code: {s.city_code} url: {s.url}' \
            ' title: {s.title} price: {s.price}' \
            ' photos: {photos_count}' \
            .format(
                s=self,
                photos_count=len(self.photos) if self.photos else 'n/a',
            )
