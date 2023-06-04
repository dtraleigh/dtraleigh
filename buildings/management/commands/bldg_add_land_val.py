"""This is used to update all buildings in the database and add the LAND_VAL value

See: https://data-wake.opendata.arcgis.com/datasets/Wake::parcels/api
"""
import requests
from django.core.management.base import BaseCommand
from buildings.models import Building


class Command(BaseCommand):

    def add_arguments(self, parser):
        # Required arguments
        parser.add_argument("offset", help="integer offset")

        # Optional arguments
        parser.add_argument("-p", "--pin", metavar="\b", )

    def handle(self, *args, **options):
        offset = options["offset"]
        pin = options["pin"]

        if not pin:
            all_bldgs = Building.objects.all()
            # freeman_house = Building.objects.get(id=107871)
            """133,656 results as of May 2022."""
            while offset < 134000:
                onek_buildings = get_buildings_w_land_val(offset)
                update_land_value(onek_buildings)
                offset += 1000
                print(str(offset))
        else:
            one_bldg = get_building_by_pin(pin)
            update_land_value([one_bldg])


def update_land_value(parcels):
    print(parcels)
    for parcel in parcels["features"]:
        try:
            known_parcel = Building.objects.get(PIN_NUM=parcel["attributes"]["PIN_NUM"])
            if not known_parcel.LAND_VAL:
                known_parcel.LAND_VAL = parcel["attributes"]["LAND_VAL"]
                known_parcel.save()
        except Exception:
            pass

        # print(parcel["attributes"]["LAND_VAL"])


def get_buildings_w_land_val(offset):
    url = f"https://maps.wakegov.com/arcgis/rest/services/Property/Parcels/MapServer/0/query?where=CITY='RAL'&" \
          f"outFields=PIN_NUM,ADDR1,PROPDESC,SITE_ADDRESS,YEAR_BUILT,TYPE_USE_DECODE,CITY,OBJECTID,LAND_VAL&" \
          f"outSR=4326&f=json&returnGeometry=false&resultOffset={str(offset)}"

    response = requests.request("GET", url, headers={}, data={})

    return response.json()


def get_building_by_pin(pin):
    url = f"https://maps.wakegov.com/arcgis/rest/services/Property/Parcels/MapServer/0/query?where=PIN_NUM={pin}&" \
          f"outFields=PIN_NUM,ADDR1,PROPDESC,SITE_ADDRESS,YEAR_BUILT,TYPE_USE_DECODE,CITY,OBJECTID,LAND_VAL&outSR=4326&" \
          f"f=json&returnGeometry=false&resultOffset=0"

    response = requests.request("GET", url, headers={}, data={})

    return response.json()