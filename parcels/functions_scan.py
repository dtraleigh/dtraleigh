import datetime
import logging
import sys

import environ
from pathlib import Path

from _decimal import Decimal
from django.contrib.gis.geos import GEOSGeometry
from django.core.paginator import Paginator

from newBernTOD.functions import send_email_notice
from parcels.models import Parcel

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
    "SITE",
    "CITY",
    "CITY_DECODE"
]


def update_parcel_is_active(list_of_objectids_scanned, test):
    # Take parcels in the DB that have been marked active. If they aren't part of the scan, change them to False.
    if not test:
        message = f"{datetime.datetime.now()}: Updating is_active for all parcels based on the recent scan.\n"
        print(message)
        logger.info(message)

        parcels_not_scanned = Parcel.objects.exclude(objectid__in=list_of_objectids_scanned)
        result_message = f"{datetime.datetime.now()}: {len(parcels_not_scanned)} parcels need to be set to inactive."
        print(result_message)
        logger.info(result_message)
        # parcels_not_scanned.update(is_active=False)

        paginator = Paginator(parcels_not_scanned, 100)

        for page_number in paginator.page_range:
            page = paginator.page(page_number)
            updates = []

            for obj in page.object_list:
                obj.is_active = False
                updates.append(obj)

            update_message = f"{datetime.datetime.now()}: Updating is_active on {len(updates)} parcels."
            print(update_message)
            logger.info(update_message)
            Parcel.objects.bulk_update(updates, ["is_active"])

        post_update_message = f"{datetime.datetime.now()}: Finished updating is_active."
        print(post_update_message)
        logger.info(post_update_message)


def scan_results_email(subject, output_message):
    send_email_notice(subject, output_message, [env("ADMIN_EMAIL")])


def difference_exists(item1, item2):
    if item1 == item2:
        return False
    return True


def set_parcel_to_active(parcel):
    parcel.is_active = True
    parcel.save()


def create_a_new_parcel(parcel_json, parcel_model, scan_report):
    deed_acres_value = parcel_json["attributes"]["DEED_ACRES"]
    deed_acres_translate = handle_deed_acres_special_case(deed_acres_value)

    try:
        if not scan_report.is_test:
            parcel_model.objects.create(pin=parcel_json["attributes"]["PIN_NUM"],
                                        objectid=parcel_json["attributes"]["OBJECTID"],
                                        reid=parcel_json["attributes"]["REID"],
                                        owner=parcel_json["attributes"]["OWNER"],
                                        geom=create_GEOSGeometry_object(parcel_json),
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
                                        is_active=True,
                                        city=parcel_json["attributes"]["CITY"],
                                        city_decode=parcel_json["attributes"]["CITY_DECODE"])
        scan_report.increment_num_parcels_created()
    except Exception as e:
        logger.exception(e)
        scan_report.add_parcel_json_issue(parcel_json, e)


def update_parcel_if_needed(parcel_json, parcel_model, scan_report):
    num_parcel_changes = 0
    update_fields = []

    try:
        # From the database
        parcel = parcel_model.objects.get(objectid=parcel_json["attributes"]["OBJECTID"])
    except Exception as e:
        print(e)
        print(f'Attempted query = parcel_model.objects.get(objectid={parcel_json["attributes"]["OBJECTID"]})')
        print(f'parcel_json["attributes"]["OBJECTID"] = {parcel_json["attributes"]["OBJECTID"]}')
        logger.exception(e)
        logger.info(f'Attempted query = parcel_model.objects.get(objectid={parcel_json["attributes"]["OBJECTID"]})')
        logger.info(f'parcel_json["attributes"]["OBJECTID"] = {parcel_json["attributes"]["OBJECTID"]}')
        logger.info(f"all_parcel_scan exited at {datetime.datetime.now()}")
        sys.exit(1)

    try:
        # From the scan
        parcel_data = parcel_json["attributes"]
        set_parcel_to_active(parcel)

        for field in fields_to_track:
            if field == "DEED_ACRES":
                item_from_json = handle_deed_acres_special_case(parcel_data["DEED_ACRES"])
            else:
                item_from_json = parcel_data[field]

            item_from_db = getattr(parcel, field.lower())

            if difference_exists(item_from_json, item_from_db):
                logger.info(f"Difference found with {parcel} and field {field}")
                logger.info(f"item_from_json: {item_from_json}, type {type(item_from_json)}")
                logger.info(f"item_from_db: {item_from_db}, type {type(item_from_db)}")
                setattr(parcel, field.lower(), parcel_data[field])
                update_fields.append(field.lower())
                num_parcel_changes += 1

        parcel_GEOSGeometry_object = create_GEOSGeometry_object(parcel_json)
        parcel_geom_has_changed = geom_has_changed(parcel, parcel_GEOSGeometry_object)
        if parcel_geom_has_changed:
            parcel.geom = parcel_GEOSGeometry_object.json
            update_fields.append("geom")
            num_parcel_changes += 1

        if num_parcel_changes > 0:
            if not scan_report.is_test:
                parcel.save(update_fields=update_fields)
            scan_report.num_changes += 1
            scan_report.increment_num_parcels_updated()

            log_update_info(parcel, update_fields)
            scan_report.parcels_updated.append(parcel)
    except Exception as e:
        scan_report.add_parcel_issue(parcel, e)


def log_update_info(parcel, update_fields):
    logger.info(f"Updated {parcel}\n")
    logger.info(f"Fields updated: {update_fields}")


def geom_has_changed(parcel, parcel_GEOSGeometry_object):
    if parcel.geom.json != parcel_GEOSGeometry_object.json:
        return True
    return False


def handle_deed_acres_special_case(deed_acres_value):
    if deed_acres_value is None:
        return None
    return Decimal(deed_acres_value).quantize(Decimal("1.000000"))


def create_GEOSGeometry_object(parcel_json):
    return GEOSGeometry(
        '{ "type": "Polygon", "coordinates": ' + str(parcel_json["geometry"]["rings"]) + ' }')


def truncate_list_for_printing(target_list):
    # size desired
    count = 20

    target_list_length = len(target_list)
    for _ in range(0, target_list_length - count):
        target_list.pop()

    if target_list_length > count:
        target_list.append("...truncated list")

    return target_list

