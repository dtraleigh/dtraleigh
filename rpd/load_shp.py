import os
from django.contrib.gis.utils import LayerMapping
from rpd.models import RaleighPoliceDistrict

raleigh_police_districts_mapping = {
    "objectid": "OBJECTID",
    "district": "DISTRICT",
    "shape_are": "Shape__Are",
    "shape_len": "Shape__Len",
    "zoneid": "ZONEID",
    "geom": "MULTIPOLYGON",
}

rpd_shp = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "Raleigh_Police_Districts", "Raleigh_Police_Districts.shp"),
)


def run_districts(verbose=True):
    lm = LayerMapping(RaleighPoliceDistrict, rpd_shp, raleigh_police_districts_mapping, transform=False)
    lm.save(strict=True, verbose=verbose)
