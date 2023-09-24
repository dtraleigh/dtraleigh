from django.core.management.base import BaseCommand

from newBernTOD.functions import query_url_with_retries
from newBernTOD.models import Parcel


def get_parcel_data_from_county(pin):
    url = (f"https://maps.wake.gov/arcgis/rest/services/Property/Parcels/MapServer/0/query?"
           f"where=PIN_NUM='{str(pin)}'&outFields=*&inSR=4326&spatialRel=esriSpatialRelIntersects&"
           f"outSR=4326&f=json&resultOffset=0")

    response = query_url_with_retries(url)

    return response.json()


class Command(BaseCommand):
    def handle(self, *args, **options):
        parcels_that_need_an_objectid = Parcel.objects.filter(objectid=None)
        
        for parcel in parcels_that_need_an_objectid:
            try:
                parcel_json = get_parcel_data_from_county(parcel.pin)["features"]
                if len(parcel_json) > 1:
                    print(f"Multiple results for {parcel.pin}")
                    continue
                elif len(parcel_json) == 1:
                    parcel.objectid = parcel_json[0]["attributes"]["OBJECTID"]
                    parcel.save()
                    print(f"Updated objectid for {parcel}")
                else:
                    print(f"{parcel} results are {parcel_json}")
            except Exception as e:
                print(e)
                print(f"Issue with {parcel}")
