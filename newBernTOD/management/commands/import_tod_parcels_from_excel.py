import logging
import pandas as pd

from django.core.management.base import BaseCommand

from newBernTOD.functions import get_geometry_by_parcel_pin, get_parcel_fields_by_pin
from newBernTOD.models import Parcel, Overlay

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

        tod_overlay = Overlay.objects.get(name="New Bern TOD")
        for tod_parcel in [p for p in Parcel.objects.all()]:
            tod_overlay.parcels.add(tod_parcel)

            if tod_parcel.geom is None:
                tod_parcel.geom = get_geometry_by_parcel_pin(tod_parcel.pin)
                tod_parcel.save()
                print(f"Updated geometry for {tod_parcel.pin}")

            try:
                parcel_data_json = get_parcel_fields_by_pin(tod_parcel.pin)
                parcel_data = parcel_data_json["features"][0]["attributes"]

                tod_parcel.reid = parcel_data["REID"]
                tod_parcel.addr1 = parcel_data["ADDR1"]
                tod_parcel.addr2 = parcel_data["ADDR2"]
                tod_parcel.addr3 = parcel_data["ADDR3"]
                tod_parcel.deed_acres = parcel_data["DEED_ACRES"]
                tod_parcel.bldg_val = parcel_data["BLDG_VAL"]
                tod_parcel.land_val = parcel_data["LAND_VAL"]
                tod_parcel.total_value_assd = parcel_data["TOTAL_VALUE_ASSD"]
                tod_parcel.propdesc = parcel_data["PROPDESC"]
                tod_parcel.year_built = parcel_data["YEAR_BUILT"]
                tod_parcel.totsalprice = parcel_data["TOTSALPRICE"]
                tod_parcel.save()
                print(f"Updated {tod_parcel}")
            except Exception as e:
                print(tod_parcel)
                print(e)
