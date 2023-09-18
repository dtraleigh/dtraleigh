import logging

import environ
from pathlib import Path

from _decimal import Decimal
from django.contrib.gis.geos import GEOSGeometry

from newBernTOD.functions import send_email_notice
from newBernTOD.models import Parcel

env = environ.Env(DEBUG=(bool, False))
BASE_DIR = Path(__file__).resolve().parent.parent
environ.Env.read_env(BASE_DIR / ".env")
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


def update_parcel_is_active(list_of_objectids_scanned, parcel_query_is_active_true):
    # Take parcels in the DB that have been marked active. If they aren't part of the scan, change them to False.
    for parcel in parcel_query_is_active_true:
        if parcel.objectid not in list_of_objectids_scanned:
            parcel.is_active = False
            parcel.save()


def scan_results_email(subject, output_message):
    send_email_notice(subject, output_message, [env("ADMIN_EMAIL")])


def difference_exists(item1, item2):
    if item1 == item2:
        return False
    return True


def set_parcel_to_active(parcel):
    parcel.is_active = True
    parcel.save()


def create_a_new_parcel(parcel_json, parcel_GEOSGeometry_object):
    deed_acres_value = parcel_json["attributes"]["DEED_ACRES"]
    deed_acres_translate = handle_deed_acres_special_case(deed_acres_value)

    Parcel.objects.create(pin=parcel_json["attributes"]["PIN_NUM"],
                          objectid=parcel_json["attributes"]["OBJECTID"],
                          reid=parcel_json["attributes"]["REID"],
                          owner=parcel_json["attributes"]["OWNER"],
                          geom=parcel_GEOSGeometry_object,
                          addr1=parcel_json["attributes"]["ADDR1"],
                          addr2=parcel_json["attributes"]["ADDR2"],
                          addr3=parcel_json["attributes"]["ADDR3"],
                          deed_acres=deed_acres_translate,
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
                          site=parcel_json["attributes"]["SITE"],
                          is_active=True)


def update_geom_if_changed(parcel, parcel_GEOSGeometry_object):
    if parcel.geom.json != parcel_GEOSGeometry_object.json:
        parcel.geom = parcel_GEOSGeometry_object.json
        parcel.save()
        return True
    return False


def handle_deed_acres_special_case(deed_acres_value):
    if deed_acres_value is None:
        return None
    return Decimal(deed_acres_value).quantize(Decimal("1.000000"))


def create_GEOSGeometry_object(parcel_json):
    return GEOSGeometry(
        '{ "type": "Polygon", "coordinates": ' + str(parcel_json["geometry"]["rings"]) + ' }')


def create_update_parcels(parcels_scanned, scan_report):
    for parcel_json in parcels_scanned:
        parcel_GEOSGeometry_object = create_GEOSGeometry_object(parcel_json)

        # If parcel does not exist, add it
        if not Parcel.objects.filter(objectid=parcel_json["attributes"]["OBJECTID"]).exists():
            try:
                if not scan_report.is_test: create_a_new_parcel(parcel_json, parcel_GEOSGeometry_object)
                scan_report.increment_num_parcels_created()
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
                    if field == "DEED_ACRES": item_from_json = handle_deed_acres_special_case(parcel_data["DEED_ACRES"])

                    if difference_exists(item_from_json, item_from_db):
                        setattr(parcel, field.lower(), parcel_data[field])
                        scan_report.increment_num_changes()

                parcel_geom_has_changed = update_geom_if_changed(parcel, parcel_GEOSGeometry_object)
                if parcel_geom_has_changed: scan_report.increment_num_changes()

                if scan_report.num_changes > 0:
                    if not scan_report.is_test: parcel.save()
                    scan_report.increment_num_parcels_updated()

                    scan_report.output_message += f"Updated {parcel}\n"
                    scan_report.parcels_updated.append(parcel)
            except Exception as e:
                scan_report.add_parcel_issue(parcel, e)
