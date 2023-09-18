import logging
from decimal import Decimal

from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import BaseCommand

from newBernTOD.functions import get_parcels_around_new_bern
from parcels.ScanReport import ScanReport
from parcels.functions_scan import update_parcel_is_active, scan_results_email, difference_exists, set_parcel_to_active, \
    create_a_new_parcel, update_geom_if_changed
from newBernTOD.models import Parcel

logger = logging.getLogger("django")

fields_to_track = [
    "REID",
    "OBJECTID",
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

list_of_objectids_scanned = []


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("-t", "--test", action="store_true", help="Run a test without making any changes.")

    def handle(self, *args, **options):
        scan_report = ScanReport("New Bern Scan Report", options["test"])

        offset = 0
        increment = 1000
        scan_report.total_parcels_in_dataset = get_parcels_around_new_bern("", True)["count"]

        print(f"Found {scan_report.total_parcels_in_dataset} parcels total in the scan area.\n")
        while offset < 1000:
            print(f"Getting parcels {offset + 1} to {offset + increment}")
            onek_parcels = get_parcels_around_new_bern(offset)
            create_update_parcels(onek_parcels["features"], scan_report)
            update_objectids_list(onek_parcels["features"])
            offset += increment

        update_parcel_is_active(list_of_objectids_scanned, Parcel.objects.filter(is_active=True))
        scan_report.send_output_message()
        print(scan_report.output_message)


def create_GEOSGeometry_object(parcel_json):
    return GEOSGeometry(
        '{ "type": "Polygon", "coordinates": ' + str(parcel_json["geometry"]["rings"]) + ' }')


def handle_deed_acres_special_case(parcel_data):
    if parcel_data["DEED_ACRES"] is None:
        return None
    return Decimal(parcel_data["DEED_ACRES"]).quantize(Decimal("1.000000"))


def create_update_parcels(new_bern_parcels, scan_report):
    for parcel_json in new_bern_parcels:
        parcel_GEOSGeometry_object = create_GEOSGeometry_object(parcel_json)

        # If parcel does not exist, add it
        if not Parcel.objects.filter(objectid=parcel_json["attributes"]["OBJECTID"]).exists():
            try:
                if not scan_report.is_test: create_a_new_parcel(parcel_json, parcel_GEOSGeometry_object)
                scan_report.num_parcels_created += 1
            except Exception as e:
                logger.exception(e)
                scan_report.add_parcel_json_issue(parcel_json, e)
        # Else, check if there is an update to the parcel and update a tracked field
        else:
            try:
                parcel = Parcel.objects.get(objectid=parcel_json["attributes"]["OBJECTID"])
                parcel_data = parcel_json["attributes"]
                set_parcel_to_active(parcel)

                for field in fields_to_track:
                    item_from_json = parcel_data[field]
                    item_from_db = getattr(parcel, field.lower())
                    if field == "DEED_ACRES": item_from_json = handle_deed_acres_special_case(parcel_data)

                    if difference_exists(item_from_json, item_from_db):
                        setattr(parcel, field.lower(), parcel_data[field])
                        scan_report.num_changes += 1

                parcel_geom_has_changed = update_geom_if_changed(parcel, parcel_GEOSGeometry_object)
                if parcel_geom_has_changed: scan_report.num_changes += 1

                if scan_report.num_changes > 0:
                    if not scan_report.is_test: parcel.save()
                    scan_report.num_parcels_updated += 1

                    scan_report.output_message += f"Updated {parcel}\n"
                    scan_report.parcels_updated.append(parcel)
            except Exception as e:
                scan_report.add_parcel_issue(parcel, e)


# def create_update_parcels2(new_bern_parcels, test):
#     num_parcels_updated = 0
#     num_parcels_created = 0
#     parcels_with_issues = []
#     parcels_updated = []
#     output_message = ""
#
#     for parcel_json in new_bern_parcels:
#         parcel_GEOSGeometry_object = GEOSGeometry(
#             '{ "type": "Polygon", "coordinates": ' + str(parcel_json["geometry"]["rings"]) + ' }')
#         # If parcel does not exist, add it
#         if not Parcel.objects.filter(objectid=parcel_json["attributes"]["OBJECTID"]).exists():
#             try:
#                 if not test: create_a_new_parcel(parcel_json, parcel_GEOSGeometry_object)
#                 num_parcels_created += 1
#             except Exception as e:
#                 logger.exception(e)
#                 output_message += f"{e}\n"
#                 output_message += f"Issue with this feature\n"
#                 output_message += f"{parcel_json}\n"
#         # Else, check if there is an update to the parcel and update a tracked field
#         else:
#             try:
#                 parcel = Parcel.objects.get(objectid=parcel_json["attributes"]["OBJECTID"])
#                 parcel_data = parcel_json["attributes"]
#                 set_parcel_to_active(parcel)
#
#                 num_changes = 0
#                 for field in fields_to_track:
#                     item_from_json = parcel_data[field]
#                     item_from_db = getattr(parcel, field.lower())
#
#                     # Rare but it happens
#                     if field == "DEED_ACRES" and parcel_data["DEED_ACRES"] is None:
#                         item_from_json = None
#                     elif field == "DEED_ACRES":
#                         item_from_json = Decimal(parcel_data["DEED_ACRES"]).quantize(Decimal("1.000000"))
#
#                     if difference_exists(item_from_json, item_from_db):
#                         setattr(parcel, field.lower(), parcel_data[field])
#                         num_changes += 1
#
#                 parcel_geom_has_changed = update_geom_if_changed(parcel, parcel_GEOSGeometry_object)
#                 if parcel_geom_has_changed: num_changes += 1
#
#                 if num_changes > 0:
#                     if not test: parcel.save()
#                     num_parcels_updated += 1
#
#                     output_message += f"Updated {parcel}\n"
#                     parcels_updated.append(parcel)
#             except Exception as e:
#                 logger.exception(e)
#                 output_message += f"{e}\n"
#                 parcels_with_issues.append(parcel)
#
#     return num_parcels_created, num_parcels_updated, parcels_with_issues, parcels_updated, output_message


def update_objectids_list(parcel_json):
    for parcel in parcel_json:
        list_of_objectids_scanned.append(parcel["attributes"]["OBJECTID"])
