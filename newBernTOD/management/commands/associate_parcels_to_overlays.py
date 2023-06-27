import logging

from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import BaseCommand

from newBernTOD.functions import get_parcels_around_new_bern
from newBernTOD.models import Parcel, NCOD, HOD

logger = logging.getLogger("django")


class Command(BaseCommand):
    def handle(self, *args, **options):
        # overlays_to_loop_through = NCOD.objects.all()
        overlays_to_loop_through = HOD.objects.all()

        # test with one first
        # kc = NCOD.objects.get(olay_name="King Charles (South)")
        # for parcel in Parcel.objects.all():
        #     parcel_center = parcel.geom.centroid
        #     if kc.geom.intersects(parcel_center):
        #         kc.parcels.add(parcel)

        for overlay in overlays_to_loop_through:
            for parcel in Parcel.objects.all():
                parcel_center = parcel.geom.centroid
                if overlay.geom.intersects(parcel_center):
                    overlay.parcels.add(parcel)
