from django.db import models
from django.contrib.postgres.fields import ArrayField


class CraigsListItem(models.Model):

    ts_created = models.DateTimeField(null=True, blank=True)
    ts_imported = models.DateTimeField(auto_now_add=True)
    session_id = models.CharField(
        max_length=50, null=True, blank=True, db_index=True,
    )
    city_code = models.CharField(
        max_length=50, null=True, blank=True, db_index=True,
    )
    url = models.URLField(
        max_length=500, null=True, blank=True, db_index=True,
    )
    title = models.CharField(
        max_length=500, null=True, blank=True,
    )

    # currency in cents
    price = models.PositiveIntegerField(
        '$ in cents', null=True, blank=True,
    )

    photos = ArrayField(models.URLField(), null=True, blank=True)

    description = models.TextField(null=True, blank=True)
