from django.core.management.base import BaseCommand

from parcels.ScanReport import ScanReport
from parcels.functions import get_freeman_parcels
from parcels.functions_scan import update_parcel_is_active, create_a_new_parcel, update_parcel_if_needed
from parcels.models import Parcel

list_of_objectids_scanned = []


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("-t", "--test", action="store_true", help="Run a test without making any changes.")

    def handle(self, *args, **options):
        scan_report = ScanReport("Freeman Report", options["test"])
        all_known_parcels = [p.objectid for p in Parcel.objects.all()]

        offset = 0
        increment = 1000
        scan_report.total_parcels_in_dataset = get_freeman_parcels("", True)["count"]

        print(f"Found {scan_report.total_parcels_in_dataset} parcels total in the scan area.\n")
        while offset < scan_report.total_parcels_in_dataset:
            print(f"Getting parcels {offset + 1} to {offset + increment}")
            onek_parcels = get_freeman_parcels(offset)

            for parcel_json in onek_parcels["features"]:
                if parcel_json["attributes"]["OBJECTID"] not in all_known_parcels:
                    create_a_new_parcel(parcel_json, Parcel, scan_report)
                else:
                    update_parcel_if_needed(parcel_json, Parcel, scan_report)

            self.update_objectids_list(onek_parcels["features"])
            offset += increment

        update_parcel_is_active(list_of_objectids_scanned, Parcel.objects.filter(is_active=True), options["test"])
        scan_report.send_output_message()
        print(scan_report.output_message)

    def update_objectids_list(self, parcel_json):
        for parcel in parcel_json:
            list_of_objectids_scanned.append(parcel["attributes"]["OBJECTID"])
