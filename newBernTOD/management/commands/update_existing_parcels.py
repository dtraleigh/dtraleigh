import logging

from django.core.management.base import BaseCommand

from newBernTOD.functions import get_parcel_fields_by_pin
from newBernTOD.models import Parcel

logger = logging.getLogger("django")


class Command(BaseCommand):
    def handle(self, *args, **options):
        all_parcels = Parcel.objects.all()

        for parcel in all_parcels:
            try:
                parcel_data_json = get_parcel_fields_by_pin(parcel.pin)
                parcel_data = parcel_data_json["features"][0]["attributes"]

                parcel.reid = parcel_data["REID"]
                parcel.addr1 = parcel_data["ADDR1"]
                parcel.addr2 = parcel_data["ADDR2"]
                parcel.addr3 = parcel_data["ADDR3"]
                parcel.deed_acres = parcel_data["DEED_ACRES"]
                parcel.bldg_val = parcel_data["BLDG_VAL"]
                parcel.land_val = parcel_data["LAND_VAL"]
                parcel.total_value_assd = parcel_data["TOTAL_VALUE_ASSD"]
                parcel.propdesc = parcel_data["PROPDESC"]
                parcel.year_built = parcel_data["YEAR_BUILT"]
                parcel.totsalprice = parcel_data["TOTSALPRICE"]
                parcel.save()
                print(f"Updated {parcel}")
            except Exception as e:
                print(parcel)
                print(e)
