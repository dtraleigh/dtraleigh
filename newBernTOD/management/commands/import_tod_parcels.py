import logging
import pandas as pd

from django.core.management.base import BaseCommand

from newBernTOD.functions import get_geometry_by_parcel_pin
from newBernTOD.models import Parcel

logger = logging.getLogger("django")


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
