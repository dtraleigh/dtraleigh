from django.db import models

# This is an auto-generated Django model module created by ogrinspect.
from django.contrib.gis.db import models


class BusRoute(models.Model):
    objectid = models.IntegerField()
    full_name = models.CharField(max_length=50, null=True)
    dir_id = models.CharField(max_length=1, null=True)
    dir_name = models.CharField(max_length=10, null=True)
    pattern = models.CharField(max_length=1, null=True)
    line_name = models.CharField(max_length=35, null=True)
    map_name = models.CharField(max_length=14, null=True)
    shape_len = models.CharField(max_length=1, null=True)
    geom = models.MultiLineStringField(srid=4326, null=True)


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
