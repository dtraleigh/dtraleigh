import logging
from datetime import datetime
from decimal import Decimal

from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import BaseCommand

from newBernTOD.functions import get_parcels_around_new_bern, send_email_notice
from newBernTOD.models import Parcel

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
    def add_arguments(self, parser):
        parser.add_argument("-t", "--test", action="store_true", help="Run a test without making any changes.")

    def handle(self, *args, **options):
        test = options["test"]
        offset = 0
        num_parcels_updated = 0
        num_parcels_created = 0
        increment = 1000
        parcels_with_issues = []
        parcels_updated = []
        num_parcels = get_parcels_around_new_bern("", True)["count"]

        print(f"Found {num_parcels} parcels total in the scan area.\n")
        while offset < num_parcels:
            print(f"Getting parcels {offset + 1} to {offset + increment}")
            onek_parcels = get_parcels_around_new_bern(offset)
            num_parcels_created_returned, num_parcels_updated_returned, parcels_with_issues_returned, parcels_updated_returned, output_message = create_update_parcels(
                onek_parcels["features"], test)
            num_parcels_created += num_parcels_created_returned
            num_parcels_updated += num_parcels_updated_returned
            parcels_with_issues.append(parcels_with_issues_returned)
            parcels_updated.append(parcels_updated_returned)
            offset += increment

        if test:
            output_message += "Test Results:\n"
        output_message += f"{str(num_parcels_created)} parcels created.\n"
        output_message += f"{str(num_parcels_updated)} parcels updated.\n"
        output_message += f"Parcels updated: {parcels_updated}\n"
        output_message += f"Check these parcels: {parcels_with_issues}\n"

        print(output_message)
        subject = "Message from New Bern TOD"

        send_email_notice(subject, output_message, ["leo@dtraleigh.com"])


def difference_exists(item1, item2):
    if item1 == item2:
        return False
    return True


def create_update_parcels(new_bern_parcels, test):
    num_parcels_updated = 0
    num_parcels_created = 0
    parcels_with_issues = []
    parcels_updated = []
    output_message = ""

    for parcel_json in new_bern_parcels:
        # Debug
        # debug = False
        # if parcel_json["attributes"]["PIN_NUM"] == "1713675460":
        #     debug = True
        #     print(f"On pin 1713675460.")
        # If parcel does not exist, add it
        if not Parcel.objects.filter(pin=parcel_json["attributes"]["PIN_NUM"]).exists():
            parcel_geom = GEOSGeometry(
                '{ "type": "Polygon", "coordinates": ' + str(parcel_json["geometry"]["rings"]) + ' }')
            try:
                if not test:
                    Parcel.objects.create(pin=parcel_json["attributes"]["PIN_NUM"],
                                          reid=parcel_json["attributes"]["REID"],
                                          owner=parcel_json["attributes"]["OWNER"],
                                          geom=parcel_geom,
                                          addr1=parcel_json["attributes"]["ADDR1"],
                                          addr2=parcel_json["attributes"]["ADDR2"],
                                          addr3=parcel_json["attributes"]["ADDR3"],
                                          deed_acres=Decimal(parcel_json["attributes"]["DEED_ACRES"]).quantize(
                                              Decimal("1.000000")),
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
                logger.exception(e)
                output_message += f"{e}\n"
                output_message += f"Issue with this feature\n"
                output_message += f"{parcel_json}\n"
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
                        # if debug:
                        #     print(f"{item_from_json} : {item_from_db}")
                        setattr(parcel, field.lower(), parcel_data[field])
                        num_changes += 1
                # Need to add a geom check
                if num_changes > 0:
                    if not test:
                        parcel.save()
                    num_parcels_updated += 1

                    output_message += f"Updated {parcel}\n"
                    parcels_updated.append(parcel)
            except Exception as e:
                logger.exception(e)
                output_message += f"{e}\n"
                parcels_with_issues.append(parcel)

    return num_parcels_created, num_parcels_updated, parcels_with_issues, parcels_updated, output_message
