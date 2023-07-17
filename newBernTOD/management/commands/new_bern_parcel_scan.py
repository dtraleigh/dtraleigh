import logging
from decimal import Decimal

from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import BaseCommand

from newBernTOD.functions import get_parcels_around_new_bern, get_parcel_fields_by_pin
from newBernTOD.models import Parcel, Overlay

logger = logging.getLogger("django")

fields_to_track = [
    "REID",
    "ADDR1",
    "ADDR2",
    "ADDR3",
    "DEED_ACRES",
    "BLDG_VAL",
    "LAND_VAL",
    "TOTAL_VALUE_ASSD",
    "PROPDESC",
    "YEAR_BUILT",
    "TOTSALPRICE",
    "SALE_DATE",
    "TYPE_AND_USE",
    "TYPE_USE_DECODE",
    "DESIGNSTYL",
    "DESIGN_STYLE_DECODE",
    "UNITS",
    "TOTSTRUCTS",
    "TOTUNITS",
    "SITE"
]


class Command(BaseCommand):
    def handle(self, *args, **options):
        offset = 0
        num_parcels_updated = 0
        num_parcels_created = 0
        parcels_with_issues = []
        parcels_updated = []

        while offset < 35000:
            print(str(offset))
            onek_parcels = get_parcels_around_new_bern(offset)
            num_parcels_created_returned, num_parcels_updated_returned, parcels_with_issues_returned, parcels_updated_returned = create_update_parcels(onek_parcels["features"])
            num_parcels_created += num_parcels_created_returned
            num_parcels_updated += num_parcels_updated_returned
            parcels_with_issues.append(parcels_with_issues_returned)
            parcels_updated.append(parcels_updated_returned)
            offset += 1000

        print(f"{str(num_parcels_created)} parcels created.")
        print(f"{str(num_parcels_updated)} parcels updated.")
        print(f"Parcels updated: {parcels_updated}")
        print(f"Check these parcels: {parcels_with_issues}")


def difference_exists(item1, item2):
    if item1 == item2:
        return False
    return True


def create_update_parcels(new_bern_parcels):
    num_parcels_updated = 0
    num_parcels_created = 0
    parcels_with_issues = []
    parcels_updated = []

    for parcel_json in new_bern_parcels:
        # If parcel does not exist, add it
        if not Parcel.objects.filter(pin=parcel_json["attributes"]["PIN_NUM"]).exists():
            parcel_geom = GEOSGeometry(
                '{ "type": "Polygon", "coordinates": ' + str(parcel_json["geometry"]["rings"]) + ' }')
            try:
                Parcel.objects.create(pin=parcel_json["attributes"]["PIN_NUM"],
                                      owner=parcel_json["attributes"]["OWNER"],
                                      geom=parcel_geom,
                                      addr1=parcel_json["attributes"]["ADDR1"],
                                      addr2=parcel_json["attributes"]["ADDR2"],
                                      addr3=parcel_json["attributes"]["ADDR3"],
                                      deed_acres=parcel_json["attributes"]["DEED_ACRES"],
                                      bldg_val=parcel_json["attributes"]["BLDG_VAL"],
                                      land_val=parcel_json["attributes"]["LAND_VAL"],
                                      total_value_assd=parcel_json["attributes"]["TOTAL_VALUE_ASSD"],
                                      propdesc=parcel_json["attributes"]["PROPDESC"],
                                      year_built=parcel_json["attributes"]["YEAR_BUILT"],
                                      totsalprice=parcel_json["attributes"]["TOTSALPRICE"],
                                      sale_date=parcel_json["attributes"]["SALE_DATE"],
                                      type_and_use=parcel_json["attributes"]["TYPE_AND_USE"],
                                      type_use_decode=parcel_json["attributes"]["TYPE_USE_DECODE"],
                                      designstyl=parcel_json["attributes"]["DESIGNSTYL"],
                                      design_style_decode=parcel_json["attributes"]["DESIGN_STYLE_DECODE"],
                                      units=parcel_json["attributes"]["UNITS"],
                                      totstructs=parcel_json["attributes"]["TOTSTRUCTS"],
                                      totunits=parcel_json["attributes"]["TOTUNITS"],
                                      site=parcel_json["attributes"]["SITE"])
                num_parcels_created += 1
            except Exception as e:
                print(e)
                print(f"Issue with this feature")
                print(parcel_json)
        # Else, check if there is an update to the parcel and update a tracked field
        else:
            try:
                parcel = Parcel.objects.get(pin=parcel_json["attributes"]["PIN_NUM"])
                parcel_data = parcel_json["attributes"]

                num_changes = 0
                for field in fields_to_track:
                    item_from_json = parcel_data[field]
                    item_from_db = getattr(parcel, field.lower())

                    if field == "DEED_ACRES":
                        item_from_json = Decimal(parcel_data["DEED_ACRES"]).quantize(Decimal("1.000000"))

                    if difference_exists(item_from_json, item_from_db):
                        setattr(parcel, field.lower(), parcel_data[field])
                        num_changes += 1
                # Need to add a geom check
                if num_changes > 0:
                    parcel.save()
                    num_parcels_updated += 1

                    print(f"Updated {parcel}")
                    parcels_updated.append(parcel)
            except Exception as e:
                # print(parcel)
                print(e)
                parcels_with_issues.append(parcel)

    return num_parcels_created, num_parcels_updated, parcels_with_issues, parcels_updated
