from django.core.management.base import BaseCommand

from parcels.ScanReport import ScanReport
from parcels.functions import get_all_RAL_parcels
from parcels.functions_scan import update_parcel_is_active, create_a_new_parcel, update_parcel_if_needed
from parcels.models import Parcel

list_of_objectids_scanned = []


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("-t", "--test", action="store_true", help="Run a test without making any changes.")

    def handle(self, *args, **options):
        scan_report = ScanReport("Wake Scan Report", options["test"])
        scan_report.known_parcel_objectids = [p.objectid for p in Parcel.objects.all()]

        offset = 0
        scan_report.total_parcels_in_dataset = get_all_RAL_parcels("", True)["count"]

        print(f"Found {scan_report.total_parcels_in_dataset} parcels total in the scan area.\n")
        while offset < scan_report.total_parcels_in_dataset:
            parcel_subset = get_all_RAL_parcels(offset)
            num_features_returned = len(parcel_subset["features"])
            print(f"Got parcels {offset} to {offset + num_features_returned}")

            for parcel_json in parcel_subset["features"]:
                if parcel_json["attributes"]["OBJECTID"] not in scan_report.known_parcel_objectids:
                    create_a_new_parcel(parcel_json, Parcel, scan_report)
                else:
                    update_parcel_if_needed(parcel_json, Parcel, scan_report)
                scan_report.add_objectid_to_known_list(parcel_json["attributes"]["OBJECTID"])

            self.update_objectids_list(parcel_subset["features"])
            offset += num_features_returned

        update_parcel_is_active(list_of_objectids_scanned, Parcel.objects.filter(is_active=True), options["test"])
        scan_report.send_output_message()
        print(scan_report.output_message)

    def update_objectids_list(self, parcel_json):
        for parcel in parcel_json:
            list_of_objectids_scanned.append(parcel["attributes"]["OBJECTID"])
