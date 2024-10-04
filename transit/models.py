from django.db import models

# This is an auto-generated Django model module created by ogrinspect.
from django.contrib.gis.db import models


class BusRoute(models.Model):
    PURPLE = "rgb(86, 53, 130)"
    ORANGE = "rgb(234, 133, 23)"
    RED = "rgb(217, 42, 28)"
    BLUE = "rgb(0, 134, 196)"
    MAGENTA = "rgb(157, 68, 137)"
    WHITE = "rgb(255, 255, 255)"
    GREEN = "rgb(4, 150, 132)"
    COLORS = (
        (PURPLE, "Purple"),
        (ORANGE, "Orange"),
        (RED, "Red"),
        (BLUE, "Blue"),
        (MAGENTA, "Magenta"),
        (WHITE, "White"),
        (GREEN, "Green"),
    )

    objectid = models.IntegerField()
    full_name = models.CharField(max_length=50, null=True, blank=True)
    dir_id = models.CharField(max_length=1, null=True, blank=True)
    dir_name = models.CharField(max_length=10, null=True, blank=True)
    pattern = models.CharField(max_length=1, null=True, blank=True)
    line_name = models.CharField(max_length=35, null=True, blank=True)
    map_name = models.CharField(max_length=14, null=True, blank=True)
    shape_len = models.CharField(max_length=1, null=True, blank=True)
    geom = models.MultiLineStringField(srid=4326, null=True, blank=True)
    route_color = models.CharField(max_length=30, choices=COLORS, default=RED)


# Auto-generated `LayerMapping` dictionary for BusRoute model
busroute_mapping = {
    'objectid': 'OBJECTID',
    'full_name': 'full_name',
    'dir_id': 'dir_id',
    'dir_name': 'dir_name',
    'pattern': 'pattern',
    'line_name': 'line_name',
    'map_name': 'map_name',
    'shape_len': 'Shape__Len',
    'geom': 'MULTILINESTRING25D',
}
