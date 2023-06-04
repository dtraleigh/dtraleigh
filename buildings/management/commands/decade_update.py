"""This is used to update the existing decades"""
from django.core.management.base import BaseCommand
from buildings.models import *
from django.core.serializers import serialize
import json


class Command(BaseCommand):
    def handle(self, *args, **options):
        # decade = Decade.objects.get(decade_name="2000s")
        # with open("buildings/geojson_files/2000s_reduced.json") as f:
        #     decade.output_geojson_reduced = f.read()
        #     decade.save()
        #     f.close()

        # decades = Decade.objects.all()
        # for decade in decades:
        #     bldgs_in_decade = Building.objects.filter(YEAR_BUILT__range=(decade.start_year, decade.end_year))
        #     decade.output_geojson = serialize("geojson", bldgs_in_decade,
        #                                       geometry_field="geom",
        #                                       fields=("YEAR_BUILT",))
        #     decade.save()

        land_val_map = CustomMap.objects.get(map_name="Land Value per Acre Map")
        with open("buildings/geojson_files/all_bldgs_land_value_deed_acres_reduced_bottom_50_removed.json") as f:
            land_val_map.output_geojson = json.loads(f.read())
            land_val_map.save()
            f.close()
