import logging

from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import BaseCommand

from newBernTOD.functions import get_ncod_overlays
from newBernTOD.models import Parcel, Overlay

logger = logging.getLogger("django")


class Command(BaseCommand):
    def handle(self, *args, **options):
        ncods = get_ncod_overlays()

        for ncod in ncods["features"]:
            if not Overlay.objects.filter(OBJECTID=ncod["attributes"]["OBJECTID"], OVERLAY="NCOD").exists():
                overlay_geom = GEOSGeometry('{ "type": "Polygon", "coordinates": ' + str(ncod["geometry"]["rings"]) + ' }')
                Overlay.objects.create(OLAY_NAME=ncod["attributes"]["OLAY_NAME"],
                                       OBJECTID=ncod["attributes"]["OBJECTID"],
                                       ZONE_CASE=ncod["attributes"]["ZONE_CASE"],
                                       ORDINANCE=ncod["attributes"]["ORDINANCE"],
                                       EFF_DATE=ncod["attributes"]["EFF_DATE"],
                                       OVERLAY=ncod["attributes"]["OVERLAY"],
                                       geom=overlay_geom)


