import environ
from pathlib import Path

from newBernTOD.functions import send_email_notice

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
