"""Check Raleigh case-tracking pages for unexpected table structure changes."""
import logging
import sys
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from prettytable import PrettyTable

from django.core.management.base import BaseCommand
from develop.models import *
from .emails import send_email_notice, email_admins

logger = logging.getLogger("django")


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def get_page_content(page_link):
    """Download page content and return a BeautifulSoup instance."""
    try:
        response = requests.get(page_link, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.content, "html.parser")

    except requests.exceptions.RequestException as e:
        logger.error(f"Connection error to {page_link}: {e}")
        sys.exit(1)


def normalize_text(text):
    """Normalize text by stripping whitespace, replacing NBSPs, and collapsing spaces."""
    return " ".join(text.replace("\xa0", " ").split())


def extract_header_row(table, *, row_index=0):
    """Extract <th> header row."""
    thead = table.find("thead")
    if not thead:
        return None
    rows = thead.find_all("tr")
    if not rows:
        return None
    header_cells = rows[row_index].find_all(["th", "td"])
    return [normalize_text(cell.get_text()) for cell in header_cells]


def compare_headers(actual, expected, label):
    """
    Compare actual header list vs expected.
    Returns None if OK, or a formatted PrettyTable diff string if mismatched.
    """
    if actual == expected:
        return None

    # Defensive: ensure actual/expected are lists
    actual = list(actual or [])
    expected = list(expected or [])

    # Compute maximum length and pad both lists
    max_len = max(len(actual), len(expected))
    actual_padded = actual + [""] * (max_len - len(actual))
    expected_padded = expected + [""] * (max_len - len(expected))

    # Create headers for the prettytable so it knows column count
    # Use generic column names so table renders nicely.
    column_names = ["Type"] + [f"Col {i+1}" for i in range(max_len)]

    table = PrettyTable()
    table.field_names = column_names

    table.add_row(["Actual"] + actual_padded)
    table.add_row(["Expected"] + expected_padded)

    return f"{label} table has changed.\n{table}\n"



# ---------------------------------------------------------
# Management Command
# ---------------------------------------------------------

class Command(BaseCommand):
    help = "Checks published Raleigh case pages for header changes."

    def add_arguments(self, parser):
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Print detailed header extraction and comparison output.",
        )

    def handle(self, *args, **options):
        debug = options.get("debug", False)

        def debug_print(msg):
            """Only print when debug mode is enabled."""
            if debug:
                self.stdout.write(msg)

        # URLs
        zon_page_link = "https://raleighnc.gov/planning/services/rezoning-process/rezoning-cases"
        tc_page_link = "https://raleighnc.gov/planning/services/text-changes/text-change-cases"
        neighbor_page_link = "https://raleighnc.gov/planning/services/rezoning-process/neighborhood-meetings"

        # Expected headers
        ZON_EXPECTED = ["Case Number, Application & Status", "Location & Map Link", "Council District", "Staff Contact"]
        TC_EXPECTED = ["Case #", "Case Name", "Description", "Status", "Contact"]
        NEIGHBOR_EXPECTED = [
            "Date & Time", "Meeting Location", "Site Location & Map",
            "Request", "Council District", "Applicant Contact", "Staff Contact"
        ]

        report_messages = []

        # ------------------------------------------
        # 1. Zoning Cases
        # ------------------------------------------
        zon_tables = get_page_content(zon_page_link).find_all("table")
        if zon_tables:
            actual = extract_header_row(zon_tables[0])
            if actual:
                debug_print(f"[DEBUG] Zoning extracted: {actual}")
                diff = compare_headers(actual, ZON_EXPECTED, "Zoning")
                if diff:
                    debug_print("[DEBUG] Difference found:\n" + diff)
                    report_messages.append(diff)

        # ------------------------------------------
        # 2. Text Change Cases (only check the first table)
        # ------------------------------------------
        tc_tables = get_page_content(tc_page_link).find_all("table")
        if tc_tables:
            actual = extract_header_row(tc_tables[0])
            if actual:
                debug_print(f"[DEBUG] Text Change extracted: {actual}")
                diff = compare_headers(actual, TC_EXPECTED, "Text Change Cases")
                if diff:
                    debug_print("[DEBUG] Difference found:\n" + diff)
                    report_messages.append(diff)

        # ------------------------------------------
        # 3. Neighborhood Meetings (skip first)
        # ------------------------------------------
        neighbor_tables = get_page_content(neighbor_page_link).find_all("table")

        for table in neighbor_tables:
            actual = extract_header_row(table)
            if not actual:
                continue

            debug_print(f"[DEBUG] Neighborhood extracted: {actual}")

            diff = compare_headers(actual, NEIGHBOR_EXPECTED, "Neighborhood Meetings")
            if diff:
                debug_print("[DEBUG] Difference found:\n" + diff)
                report_messages.append(diff)

        # ------------------------------------------
        # Email if differences found
        # ------------------------------------------
        if report_messages:
            full_report = "\n".join(report_messages)

            debug_print("[DEBUG] Sending email notification.")
            send_email_notice(full_report, email_admins())

            self.stdout.write(self.style.WARNING("Differences detected – email sent."))
        else:
            if debug:
                self.stdout.write(self.style.SUCCESS("All table headers match expectations."))
            # When NOT in debug mode, cron stays silent unless something changed.
