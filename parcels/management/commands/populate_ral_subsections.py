import sys

from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import BaseCommand

import json

from parcels.models import RaleighSubsection


def get_list_of_features(geojson_file):
    with open(geojson_file) as file:
        data = json.load(file)

    return data["features"]


class Command(BaseCommand):

    def add_arguments(self, parser):
        # parser.add_argument("-t", "--test", action="store_true", help="Run a test without making any changes.")
        pass

    def handle(self, *args, **options):
        geojsons_to_go_through = ["parcels/resources/Raleigh_Planning_Jurisdiction_big_100.geojson", 
                                  "parcels/resources/Raleigh_Planning_Jurisdiction_small.geojson"]
        
        for geojson_file in geojsons_to_go_through:
            list_of_features = get_list_of_features(geojson_file)

            for feature in list_of_features:
                try:
                    RaleighSubsection.objects.create(geom=GEOSGeometry(str(feature["geometry"])))
                except Exception as e:
                    print(e)
                    print(feature)
                    sys.exit(0)
