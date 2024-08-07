import logging
from datetime import datetime
from array import *

from parcels.functions_scan import scan_results_email, truncate_list_for_printing
from parcels.models import Parcel

logger = logging.getLogger("django")


class ScanReport:
    def __init__(self, report_name, is_test, parcel_model):
        self.report_name = report_name
        self.model_name = parcel_model
        self.intro_message = ""
        self.output_message = ""
        self.num_parcels_created = 0
        self.num_parcels_updated = 0
        self.parcels_updated = []
        self.parcels_with_issues = []
        self.total_parcels_in_dataset = 0
        self.is_test = is_test
        self.list_of_objectids_scanned = array("i", [])
        self.num_changes = 0
        self.start_time = datetime.now()
        self.end_time = None
        self.known_parcel_objectids = array("i", [])

    def add_parcel_json_issue(self, parcel_json, e):
        self.output_message += f"{e}\n"
        self.output_message += f"Issue with this feature\n"
        self.output_message += f"{parcel_json}\n"

    def add_parcel_issue(self, parcel, e):
        logger.exception(e)
        self.output_message += f"{e}\n"
        self.parcels_with_issues.append(parcel)

    def send_output_message(self):
        parcels_updated_print = truncate_list_for_printing(self.parcels_updated)
        parcels_with_issues_print = truncate_list_for_printing(self.parcels_with_issues)
        self.end_time = datetime.now()

        if self.is_test:
            self.output_message += "Test Results:\n"
        self.output_message += f"Start time: {self.start_time}\n"
        self.output_message += f"End time: {self.end_time}\n"
        self.output_message += f"{str(self.num_parcels_created)} parcels created.\n"
        self.output_message += f"{str(self.num_parcels_updated)} parcels updated.\n"
        self.output_message += f"Parcels updated: {parcels_updated_print}\n"
        self.output_message += f"Check these parcels: {parcels_with_issues_print}\n"
        self.output_message += f"Total parcels in dataset: {self.total_parcels_in_dataset}\n"
        self.output_message += f"Total active parcels in DB: {self.model_name.objects.filter(is_active=True).count()}"
        subject = f"Message from {self.report_name}"

        scan_results_email(subject, self.output_message)
        logger.info(self.output_message)
        print(self.output_message)

    def send_intro_message(self, is_test):
        self.intro_message = f"{self.report_name} starting at {self.start_time}. is_test = {str(is_test)}"
        subject = f"Message from {self.report_name}"

        scan_results_email(subject, self.intro_message)
        logger.info(self.intro_message)
        print(self.intro_message)

    def increment_num_parcels_created(self):
        self.num_parcels_created += 1

    def increment_num_changes(self):
        self.num_changes += 1

    def increment_num_parcels_updated(self):
        self.num_parcels_updated += 1

    def add_objectid_to_known_list(self, objectid):
        self.known_parcel_objectids.append(objectid)
