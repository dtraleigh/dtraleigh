import os
from django.contrib.gis.utils import LayerMapping
from .models import ShapefileRoute

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

GoRaleigh_Bus_Routes_shp = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "GoRaleigh_Bus_Routes", "GoRaleigh_Bus_Routes.shp"),
)


def run(verbose=True):
    lm = LayerMapping(ShapefileRoute, GoRaleigh_Bus_Routes_shp, busroute_mapping, transform=True)
    lm.save(strict=True, verbose=verbose)
