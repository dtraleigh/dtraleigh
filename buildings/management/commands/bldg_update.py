"""This is used to update all buildings (parcels) from the given API endpoint.
It should update any existing entries as well as add new ones.
Results include:
outFields: PIN_NUM,ADDR1,PROPDESC,SITE_ADDRESS,YEAR_BUILT,TYPE_USE_DECODE,CITY,OBJECTID
CITY='RAL'

See: https://data-wake.opendata.arcgis.com/datasets/Wake::parcels/api
"""
import requests
from django.core.management.base import BaseCommand
from buildings.models import Building
from django.contrib.gis.geos import GEOSGeometry


class Command(BaseCommand):
    def handle(self, *args, **options):
        """133,656 results as of May 2022."""
        offset = 0
        while offset < 134000:
            print(str(offset))
            onek_buildings = get_buildings(offset)
            create_update_buildings(onek_buildings)
            offset += 1000

        # For testing
        # freeman_house_pin = "1713172921"
        # freeman_house_info = get_buildings_test(freeman_house_pin)
        # create_update_buildings(freeman_house_info)


def create_update_buildings(buildings):
    for building in buildings["features"]:
        # Check if we already have it.
        building_known = Building.objects.filter(objectid=building["attributes"]["OBJECTID"])
        if building_known.exists():
            known_bldg = Building.objects.get(objectid=building["attributes"]["OBJECTID"])
            known_bldg.geom = update_geom(building["geometry"])
            known_bldg.LAND_VAL = building["attributes"]["LAND_VAL"]
            known_bldg.DEED_ACRES = building["attributes"]["DEED_ACRES"]
            known_bldg.save()
        # else create it
        else:
            geometry = update_geom(building["geometry"])
            if geometry:
                try:
                    Building.objects.create(
                        objectid=building["attributes"]["OBJECTID"],
                        PIN_NUM=building["attributes"]["PIN_NUM"],
                        ADDR1=building["attributes"]["ADDR1"],
                        PROPDESC=building["attributes"]["PROPDESC"],
                        SITE_ADDRESS=building["attributes"]["SITE_ADDRESS"],
                        YEAR_BUILT=building["attributes"]["YEAR_BUILT"],
                        TYPE_USE_DECODE=building["attributes"]["TYPE_USE_DECODE"],
                        CITY=building["attributes"]["CITY"],
                        LAND_VAL=building["attributes"]["LAND_VAL"],
                        DEED_ACRES=building["attributes"]["DEED_ACRES"],
                        geom=geometry,
                    )
                except Exception as e:
                    print(e)
                    print(building)


def get_buildings(offset):
    url = f"http://maps.wakegov.com/arcgis/rest/services/Property/Parcels/MapServer/0/query?where=CITY='RAL'&" \
          f"outFields=PIN_NUM,ADDR1,PROPDESC,SITE_ADDRESS,YEAR_BUILT,TYPE_USE_DECODE,CITY,OBJECTID,LAND_VAL,DEED_ACRES&" \
          f"outSR=4326&f=json&resultOffset={str(offset)}"

    response = requests.request("GET", url, headers={}, data={})

    return response.json()


def update_geom(geometry):
    """Take in a geometry and return the json to create the Polygon"""
    try:
        bldg = GEOSGeometry('{ "type": "Polygon", "coordinates": ' + str(geometry["rings"]) + ' }')
    except Exception:
        # print(geometry)
        bldg = None

    return bldg


def get_buildings_test(pin_num):
    url = f"http://maps.wakegov.com/arcgis/rest/services/Property/Parcels/MapServer/0/query?where=PIN_NUM={pin_num}&" \
          f"outFields=PIN_NUM,ADDR1,PROPDESC,SITE_ADDRESS,YEAR_BUILT,TYPE_USE_DECODE,CITY,OBJECTID,LAND_VAL,DEED_ACRES&" \
          f"outSR=4326&f=json&resultOffset=0"

    response = requests.request("GET", url, headers={}, data={})

    return response.json()
