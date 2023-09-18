import logging

from parcels.functions_scan import scan_results_email

logger = logging.getLogger("django")


class ScanReport:
    def __init__(self, report_name, is_test):
        self.report_name = report_name
        self.output_message = ""
        self.num_parcels_created = 0
        self.num_parcels_updated = 0
        self.parcels_updated = []
        self.parcels_with_issues = []
        self.total_parcels_in_dataset = 0
        self.is_test = is_test
        self.list_of_objectids_scanned = []
        self.output_message = ""
        self.num_changes = 0

    def add_parcel_json_issue(self, parcel_json, e):
        self.output_message += f"{e}\n"
        self.output_message += f"Issue with this feature\n"
        self.output_message += f"{parcel_json}\n"

    def add_parcel_issue(self, parcel, e):
        logger.exception(e)
        self.output_message += f"{e}\n"
        self.parcels_with_issues.append(parcel)

    def send_output_message(self):
        if self.is_test:
            self.output_message += "Test Results:\n"
        self.output_message += f"{str(self.num_parcels_created)} parcels created.\n"
        self.output_message += f"{str(self.num_parcels_updated)} parcels updated.\n"
        self.output_message += f"Parcels updated: {self.parcels_updated}\n"
        self.output_message += f"Check these parcels: {self.parcels_with_issues}\n"
        subject = f"Message from {self.report_name}"

        scan_results_email(subject, self.output_message)
