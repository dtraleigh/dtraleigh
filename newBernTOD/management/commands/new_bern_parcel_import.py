import logging

from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import BaseCommand

from newBernTOD.functions import get_parcels_around_new_bern
from newBernTOD.models import Parcel, Overlay

logger = logging.getLogger("django")


class Command(BaseCommand):
    def handle(self, *args, **options):
        offset = 0
        while offset < 10000:
            print(str(offset))
            onek_parcels = get_parcels_around_new_bern(offset)
            create_update_parcels(onek_parcels["features"])
            offset += 1000


def create_update_parcels(new_bern_parcels):
    for parcel in new_bern_parcels:
        if not Parcel.objects.filter(pin=parcel["attributes"]["PIN_NUM"]).exists():
            parcel_geom = GEOSGeometry(
                '{ "type": "Polygon", "coordinates": ' + str(parcel["geometry"]["rings"]) + ' }')
            Parcel.objects.create(pin=parcel["attributes"]["PIN_NUM"],
                                  owner=parcel["attributes"]["OWNER"],
                                  geom=parcel_geom,
                                  addr1=parcel["attributes"]["ADDR1"],
                                  addr2=parcel["attributes"]["ADDR2"],
                                  addr3=parcel["attributes"]["ADDR3"],
                                  deed_acres=parcel["attributes"]["DEED_ACRES"],
                                  bldg_val=parcel["attributes"]["BLDG_VAL"],
                                  land_val=parcel["attributes"]["LAND_VAL"],
                                  total_value_assd=parcel["attributes"]["TOTAL_VALUE_ASSD"],
                                  propdesc=parcel["attributes"]["PROPDESC"],
                                  year_built=parcel["attributes"]["YEAR_BUILT"],
                                  totsalprice=parcel["attributes"]["TOTSALPRICE"])
