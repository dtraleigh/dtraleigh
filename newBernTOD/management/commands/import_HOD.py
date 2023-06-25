import logging

from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import BaseCommand

from newBernTOD.functions import get_hod_general_overlays, get_hod_streetside_overlays
from newBernTOD.models import Parcel, Overlay

logger = logging.getLogger("django")


class Command(BaseCommand):
    def handle(self, *args, **options):
        hods_general = get_hod_general_overlays()

        for hod in hods_general["features"]:
            if not Overlay.objects.filter(OBJECTID=hod["attributes"]["OBJECTID"], OVERLAY="HOD-G").exists():
                overlay_geom = GEOSGeometry('{ "type": "Polygon", "coordinates": ' + str(hod["geometry"]["rings"]) + ' }')
                Overlay.objects.create(OLAY_NAME=hod["attributes"]["OLAY_NAME"],
                                       OBJECTID=hod["attributes"]["OBJECTID"],
                                       ZONE_CASE=hod["attributes"]["ZONE_CASE"],
                                       ORDINANCE=hod["attributes"]["ORDINANCE"],
                                       EFF_DATE=hod["attributes"]["EFF_DATE"],
                                       OVERLAY=hod["attributes"]["OVERLAY"],
                                       geom=overlay_geom)

        hods_streetside = get_hod_streetside_overlays()

        for hod in hods_streetside["features"]:
            if not Overlay.objects.filter(OBJECTID=hod["properties"]["OBJECTID"], OVERLAY="HOD-S").exists():
                overlay_geom = GEOSGeometry('{ "type": "Polygon", "coordinates": ' + str(hod["geometry"]["coordinates"]) + ' }')
                Overlay.objects.create(OLAY_NAME=hod["properties"]["OLAY_NAME"],
                                       OBJECTID=hod["properties"]["OBJECTID"],
                                       ZONE_CASE=hod["properties"]["ZONE_CASE"],
                                       ORDINANCE=hod["properties"]["ORDINANCE"],
                                       EFF_DATE=hod["properties"]["EFF_DATE"],
                                       OVERLAY=hod["properties"]["OVERLAY"],
                                       geom=overlay_geom)



