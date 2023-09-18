import environ
from pathlib import Path

from _decimal import Decimal

from newBernTOD.functions import send_email_notice
from newBernTOD.models import Parcel

env = environ.Env(DEBUG=(bool, False))
BASE_DIR = Path(__file__).resolve().parent.parent
environ.Env.read_env(BASE_DIR / ".env")


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
    Parcel.objects.create(pin=parcel_json["attributes"]["PIN_NUM"],
                          objectid=parcel_json["attributes"]["OBJECTID"],
                          reid=parcel_json["attributes"]["REID"],
                          owner=parcel_json["attributes"]["OWNER"],
                          geom=parcel_GEOSGeometry_object,
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
                          site=parcel_json["attributes"]["SITE"],
                          is_active=True)


def update_geom_if_changed(parcel, parcel_GEOSGeometry_object):
    if parcel.geom.json != parcel_GEOSGeometry_object.json:
        parcel.geom = parcel_GEOSGeometry_object.json
        parcel.save()
        return True
    return False
