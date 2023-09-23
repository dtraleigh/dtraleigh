from django.core.management.base import BaseCommand

from parcels.ScanReport import ScanReport
from parcels.functions import get_all_parcels
from parcels.functions_scan import update_parcel_is_active, create_update_parcels
from parcels.models import Parcel

list_of_objectids_scanned = []


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("-t", "--test", action="store_true", help="Run a test without making any changes.")

    def handle(self, *args, **options):
        scan_report = ScanReport("Wake Scan Report", options["test"])

        offset = 0
        increment = 1000
        scan_report.total_parcels_in_dataset = get_all_parcels("", True)["count"]

        print(f"Found {scan_report.total_parcels_in_dataset} parcels total in the scan area.\n")
        while offset < scan_report.total_parcels_in_dataset:
            print(f"Getting parcels {offset + 1} to {offset + increment}")
            onek_parcels = get_all_parcels(offset)
            create_update_parcels(onek_parcels["features"], scan_report, Parcel)
            self.update_objectids_list(onek_parcels["features"])
            offset += increment

        update_parcel_is_active(list_of_objectids_scanned, Parcel.objects.filter(is_active=True), options["test"])
        scan_report.send_output_message()
        print(scan_report.output_message)

    def update_objectids_list(self, parcel_json):
        for parcel in parcel_json:
            list_of_objectids_scanned.append(parcel["attributes"]["OBJECTID"])
