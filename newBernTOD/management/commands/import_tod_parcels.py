import logging
import sys

import requests
import pandas as pd
from django.contrib.gis.geos import GEOSGeometry

from django.core.management.base import BaseCommand

from newBernTOD.models import Parcel

logger = logging.getLogger("django")


def get_geometry_by_parcel_pin(pin):
    url = f"https://maps.wakegov.com/arcgis/rest/services/Property/Parcels/MapServer/0/query?geometryType" \
          f"=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outSR=4326&f=json&outFields" \
          f"=*&where=PIN_NUM={pin}"

    response = requests.request("GET", url, headers={}, data={})

    if response.status_code == 200:
        try:
            parcel_geometry_json = response.json()["features"][0]["geometry"]
            return GEOSGeometry('{ "type": "Polygon", "coordinates": ' + str(parcel_geometry_json["rings"]) + ' }')
        except KeyError as e:
            print(e)
            print(response.json())
            return None
        except IndexError as e:
            print(e)
            print(f"Pin: {pin}")
            print(response.json())
    return None


class Command(BaseCommand):
    def handle(self, *args, **options):
        data = pd.read_excel("newBernTOD/management/commands/Import Z-92-22 Parcels.xlsx")

        for index in data.index:
            # print(data["PIN"][index], data["Property Address"][index])
            if not Parcel.objects.filter(pin=data["PIN"][index]).exists():
                Parcel.objects.create(property_address=data["Property Address"][index],
                                      pin=data["PIN"][index],
                                      acres=data["Acres"][index],
                                      owner=data["Owner"][index],
                                      curr_zoning=data["Current Zoning"][index],
                                      prop_zoning=data["Proposed Zoning"][index])

        for tod_parcel in [p for p in Parcel.objects.all()]:
            if tod_parcel.geom is None:
                tod_parcel.geom = get_geometry_by_parcel_pin(tod_parcel.pin)
                tod_parcel.save()
                print(f"Updated geometry for {tod_parcel.pin}")
            # else:
            #     print(f"Skipping {tod_parcel.pin} as we already know the geometry")
