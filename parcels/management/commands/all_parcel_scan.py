import datetime
import logging

from django.core.management.base import BaseCommand

from parcels.ScanReport import ScanReport
from parcels.functions import get_all_RAL_parcels
from parcels.functions_scan import update_parcel_is_active, create_a_new_parcel, update_parcel_if_needed
from parcels.models import Parcel

logger = logging.getLogger("django")
list_of_objectids_scanned = []


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("-t", "--test", action="store_true", help="Run a test without making any changes.")
        parser.add_argument("-o", "--offset", help="Sets the offset for the api call.")
        parser.add_argument("-u", "--update_only", action="store_true",
                            help="Update is_active only. Skip parcel update/create steps.")

    def handle(self, *args, **options):
        scan_report = ScanReport("RAL Scan Report", options["test"], Parcel)
        scan_report.send_intro_message(options["test"])
        scan_report.known_parcel_objectids = [p.objectid for p in Parcel.objects.all().iterator()]

        offset = 0
        if options["offset"]:
            offset = int(options["offset"])

        scan_report.total_parcels_in_dataset = get_all_RAL_parcels("", True)["count"]
        total_message = (f"{datetime.datetime.now()}: Found {scan_report.total_parcels_in_dataset} parcels total in "
                         f"the scan area.\n")
        print(total_message)
        logger.info(total_message)

        while offset < scan_report.total_parcels_in_dataset:
            parcel_subset = get_all_RAL_parcels(offset)
            num_features_returned = len(parcel_subset["features"])
            got_message = f"{datetime.datetime.now()}: Got parcels {offset} to {offset + num_features_returned}"
            print(got_message)
            logger.info(got_message)

            for parcel_json in parcel_subset["features"]:
                if not options["update_only"]:
                    if parcel_json["attributes"]["OBJECTID"] not in scan_report.known_parcel_objectids:
                        create_a_new_parcel(parcel_json, Parcel, scan_report)
                        scan_report.add_objectid_to_known_list(parcel_json["attributes"]["OBJECTID"])
                    else:
                        update_parcel_if_needed(parcel_json, Parcel, scan_report)
                else:
                    scan_report.add_objectid_to_known_list(parcel_json["attributes"]["OBJECTID"])

            self.update_objectids_list(parcel_subset["features"])
            offset += num_features_returned

        update_parcel_is_active(list_of_objectids_scanned, options["test"], Parcel)
        scan_report.send_output_message()

    def update_objectids_list(self, parcel_json):
        for parcel in parcel_json:
            list_of_objectids_scanned.append(parcel["attributes"]["OBJECTID"])
