import logging
import requests
import sys
import re
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz
from datetime import datetime

from django.core.management.base import BaseCommand

from develop.management.commands.actions import *
from develop.management.commands.location import *
from develop.models import *

logger = logging.getLogger("django")


class Command(BaseCommand):
    def handle(self, *args, **options):
        """Development Site Scraper"""
        control = Control.objects.get(id=1)
        if control.scrape:
            n = datetime.now().strftime("%H:%M %m-%d-%y")
            logger.info(f"{n}: Web scrape started.")

            sr_page_link = "https://raleighnc.gov/services/zoning-planning-and-development/site-review-cases"
            zon_page_link = "https://raleighnc.gov/planning/services/rezoning-process/rezoning-cases"
            tc_page_link = "https://raleighnc.gov/planning/services/text-changes/text-change-cases"
            neighbor_page_link = "https://raleighnc.gov/planning/services/rezoning-process/neighborhood-meetings"

            zoning_requests(get_page_content(zon_page_link))
            # admin_alternates(get_page_content(aad_page_link))
            text_changes_cases(get_page_content(tc_page_link))
            #site_reviews(get_page_content(sr_page_link)) # Site review moved to the dev portal.
            neighborhood_meetings(get_page_content(neighbor_page_link))
            # design_alternate_cases(get_page_content(da_page_link))

            logger.info(f"{n}: Web scrape finished.")


def get_page_content(page_link):
    n = datetime.now().strftime("%H:%M %m-%d-%y")

    try:
        page_response = requests.get(page_link, timeout=10)
    except requests.exceptions.RequestException as e:
        logger.info(f"{n}: Connection problem to {page_link}")
        logger.info(e)
        sys.exit(1)

    if page_response.status_code == 200:
        return BeautifulSoup(page_response.content, "html.parser")
    else:
        message = f"scrape.get_page_content did not return 200 at {n}.\n"
        message += f"link: {page_link}"
        send_email_notice(message, email_admins())
        return None


def get_rows_in_table(table, page):
    try:
        table_tbody = table.find("tbody")
        table_rows = table_tbody.find_all("tr", recursive=False)
        return table_rows
    except Exception as e:
        print(e)
        print(f"Problem getting to a table trs on page, {page}")
        if table:
            print(f"table: {table}")
        if table_tbody:
            print(f"table_tbody: {table_tbody}")
        if table_rows:
            print(f"rows: {table_rows}")


def get_case_number_from_row(row_tds):
    try:
        # If the case number is a link:
        case_number = row_tds[0].find("a").string
        return case_number
    except Exception:
        # in rare cases the case number is not a link
        return row_tds[0].string


def get_generic_link(content):
    # This is used to grab the hyperlink out of a snippet of code
    # This is used to grab the hyperlink out of a snippet of code
    if len(content.find_all("a")) == 0:
        return None
    elif len(content.find_all("a")) == 1:
        url = content.find("a")["href"].strip().replace(" ", "%20")

        # Some urls are relative so let's complete them
        if url[0] == "/":
            return "https://raleighnc.gov" + url
        return url
    elif len(content.find_all("a")) > 1:
        # for multiple entries, just take the first
        first_url = content.find("a")["href"].strip().replace(" ", "%20")
        url = first_url.strip().replace(" ", "%20")

        # Some urls are relative so let's complete them
        if url[0] == "/":
            return "https://raleighnc.gov" + url
        return url
    else:
        return None


def get_generic_text(content):
    """Extract text from HTML content, preserving line breaks and spacing.

    Handles <br> tags by converting them to spaces, and cleans up extra whitespace.

    Args:
        content: BeautifulSoup element

    Returns:
        Cleaned text string, or None if extraction fails
    """
    try:
        # Replace <br> tags with spaces before extracting text
        for br in content.find_all("br"):
            br.replace_with(" ")

        # Get the text and clean up multiple spaces
        text = content.get_text().strip()

        # Replace multiple spaces/newlines with a single space
        text = " ".join(text.split())

        return text if text else None

    except Exception as e:
        logger.info(f"get_generic_text error: {e}")
        return None

# Deprecated after removing contact and contact_url
# def get_contact_url(content):
#     # contact urls are relative
#     # Ex: "<td><a href="/directory?action=search&amp;firstName=Jason&amp;lastName=Hardin">Hardin</a></td>"
#     if content.find("a"):
#         contact = content.find("a")["href"].replace(" ", "")
#         return f"https://raleighnc.gov{contact}"
#     else:
#         return None


def determine_if_known_case(known_cases, item1, item2):
    """Go through all the cases. Use item1 and item2 to find a match.
    If we have a fuzzy match, return the case from our known list.
    Else, return none
    Criteria of a match:
    1. fuzz.ratio(case_number, sr_case.case_number) > 90
    2. fuzz.ratio(project_name, sr_case.project_name) > 90"""
    for case in known_cases:
        total_score = 0
        if isinstance(case, NeighborhoodMeeting):
            item1_score = fuzz.ratio(item1.lower(), case.meeting_datetime_details.lower())
            item2_score = fuzz.ratio(item2.lower(), case.rezoning_site_address.lower())
        else:
            item1_score = fuzz.ratio(item1.lower(), case.case_number.lower())
            item2_score = fuzz.ratio(item2.lower(), case.project_name.lower())

        if item1_score == 100 and item2_score >= 90:
            return case

    return None


def site_reviews(page_content):
    if page_content:
        sr_tables = page_content.find_all("table")

        for sr_table in sr_tables:
            sr_rows = get_rows_in_table(sr_table, "SR")

            # For each row, get the values then check if we already know about this item
            # If we do not, then add it to the DB
            # If we do, check for differences and update it
            for sr_row in sr_rows:
                row_tds = sr_row.find_all("td")

                # New 2022 layout (dropped the CAC column)
                if len(row_tds) == 4:
                    case_number = get_case_number_from_row(row_tds)
                    case_url = get_generic_link(row_tds[0])

                    project_name = get_generic_text(row_tds[1])
                    status = get_generic_text(row_tds[2])
                elif len(row_tds) == 5:
                    case_number = get_case_number_from_row(row_tds)
                    case_url = get_generic_link(row_tds[0])

                    project_name = get_generic_text(row_tds[1])
                    status = get_generic_text(row_tds[3])

                # If any of these variables are None, log it and move on.
                if not case_number or not project_name:
                    acked = ["No Case #", "ASR-0056-", "ASR-0075-2021", "\xa0"]
                    if case_number not in acked:
                        scraped_info = [["row_tds", row_tds],
                                        ["case_number", case_number],
                                        ["case_url", case_url],
                                        ["project_name", project_name],
                                        ["status", status]]
                        message = "scrape.site_reviews: Problem scraping this row\n"
                        message += str(scraped_info)
                        logger.info(message)

                        send_email_notice(message, email_admins())
                    continue

                known_sr_cases = SiteReviewCase.objects.all()

                known_sr_case = determine_if_known_case(known_sr_cases, case_number, project_name)

                # if known_sr_case was found, check for differences
                # if known_sr_case was not found, then we assume a new one was added
                # need to create
                if known_sr_case:
                    # Check for difference between known_sr_case and the variables
                    # Assume that the sr_case number doesn't change.
                    if (
                            not fields_are_same(known_sr_case.case_url, case_url) or
                            not fields_are_same(known_sr_case.project_name, project_name) or
                            not fields_are_same(known_sr_case.status, status)
                    ):
                        known_sr_case.case_url = case_url
                        known_sr_case.project_name = project_name
                        known_sr_case.status = status

                        known_sr_case.save()
                        logger.info("**********************")
                        logger.info("Updating a site case (" + str(known_sr_case) + ")")
                        logger.info("scrape case_number:" + str(case_number))
                        logger.info("scrape project_name:" + str(project_name))
                        logger.info("**********************")

                else:
                    # create a new instance
                    logger.info("**********************")
                    logger.info("Creating new site case")
                    logger.info("case_number:" + case_number)
                    logger.info("project_name:" + project_name)
                    logger.info("**********************")

                    SiteReviewCase.objects.create(case_number=case_number,
                                                  case_url=case_url,
                                                  project_name=project_name,
                                                  status=status)


def admin_alternates(page_content):
    if page_content:
        aads_tables = page_content.find_all("table")

        for aads_table in aads_tables:
            aads_rows = get_rows_in_table(aads_table, "AAD")

            # For each row, get the values then check if we already know about this item
            # If we do not, then add it to the DB
            # If we do, check for differences and update if
            for aads_row in aads_rows:
                row_tds = aads_row.find_all("td")

                case_number = get_case_number_from_row(row_tds)
                if case_number != "No cases at this time.":
                    case_url = get_generic_link(row_tds[0])
                    project_name = get_generic_text(row_tds[1])
                    status = get_generic_text(row_tds[2])

                    # If any of these variables are None, log it and move on.
                    if not case_number or not case_url or not project_name or not status:
                        scraped_info = [["row_tds", row_tds],
                                        ["case_number", case_number],
                                        ["case_url", case_url],
                                        ["project_name", project_name],
                                        ["status", status]]
                        message = "scrape.admin_alternates: Problem scraping this row"
                        message += scraped_info
                        logger.info(message)
                        send_email_notice(message, email_admins())

                        continue

                    known_aad_cases = AdministrativeAlternate.objects.all()
                    known_aad_case = determine_if_known_case(known_aad_cases, case_number, project_name)

                    # if known_tc_case was found, check for differences
                    # if known_tc_case was not found, then we assume a new one was added
                    # need to create
                    if known_aad_case:
                        # Check for difference between known_tc_case and the variables
                        # Assume that the aad_case number doesn't change.
                        if (
                                not fields_are_same(known_aad_case.case_url, case_url) or
                                not fields_are_same(known_aad_case.project_name, project_name) or
                                not fields_are_same(known_aad_case.status, status)
                        ):
                            known_aad_case.case_url = case_url
                            known_aad_case.project_name = project_name
                            known_aad_case.status = status

                            known_aad_case.save()
                            logger.info("**********************")
                            logger.info("Updating an AAD case (" + str(known_aad_case) + ")")
                            logger.info("scrape case_number:" + case_number)
                            logger.info("scrape project_name:" + project_name)
                            logger.info("**********************")

                    else:
                        # create a new instance
                        logger.info("**********************")
                        logger.info("Creating new AAD case")
                        logger.info("case_number:" + case_number)
                        logger.info("project_name:" + project_name)
                        logger.info("**********************")

                        AdministrativeAlternate.objects.create(case_number=case_number,
                                                               case_url=case_url,
                                                               project_name=project_name,
                                                               status=status)


def validate_table_headers(table_thead):
    """Extract and validate table headers.

    Supports both td and th header elements and returns the header texts.

    Args:
        table_thead: BeautifulSoup thead element

    Returns:
        List of header text strings, or None if headers are invalid
    """
    if not table_thead:
        return None

    # Try to find th elements first (modern tables), then fall back to td
    thead_row = table_thead.find_all("th")
    if not thead_row:
        thead_row = table_thead.find_all("td")

    if not thead_row:
        return None

    headers = [header.get_text().strip() for header in thead_row]
    return headers if len(headers) > 0 else None


def extract_text_change_row_data(row_tds):
    """Extract all data fields from a text change case row.
    TC_EXPECTED = ["Case #", "Case Name", "Description", "Status", "Contact"]

    Args:
        row_tds: List of BeautifulSoup td elements from the row

    Returns:
        Dictionary with extracted data or None if extraction fails
    """
    if len(row_tds) < 4:
        return None

    case_number = get_case_number_from_row(row_tds)
    case_url = get_generic_link(row_tds[0])
    project_name = get_generic_text(row_tds[1])
    description = get_generic_text(row_tds[2])
    status = get_generic_text(row_tds[3])

    return {
        "case_number": case_number,
        "case_url": case_url,
        "project_name": project_name,
        "description": description,
        "status": status
    }


def validate_text_change_data(data):
    """Validate that all required fields are present.

    Args:
        data: Dictionary with text change case data

    Returns:
        Boolean indicating if data is valid
    """
    if not data:
        return False

    required_fields = ["case_number", "case_url", "project_name", "status"]
    return all(data.get(field) for field in required_fields)


def handle_text_change_validation_error(row_tds, data):
    """Log and send email notification for text change scraping errors.

    Args:
        row_tds: List of td elements
        data: Dictionary with extracted data
    """
    scraped_info = [
        ["case_number", data.get("case_number")],
        ["case_url", data.get("case_url")],
        ["project_name", data.get("project_name")],
        ["description", data.get("description")],
        ["status", data.get("status")]
    ]
    message = "scrape.text_changes_cases: Problem scraping this row\n" + str(scraped_info)
    logger.info(message)
    send_email_notice(message, email_admins())


def check_for_no_active_cases(case_number):
    """Check if case number indicates no active cases.

    Args:
        case_number: Case number string

    Returns:
        Boolean indicating if this is a "no active cases" sentinel
    """
    return case_number == "No active cases"


def update_text_change_if_changed(known_tc_case, case_url, project_name, description, status):
    """Update text change case if any fields have changed.

    Args:
        known_tc_case: TextChangeCase database object
        case_url: New case URL
        project_name: New project name
        description: New description
        status: New status

    Returns:
        Boolean indicating if update occurred
    """
    if (not fields_are_same(known_tc_case.case_url, case_url) or
            not fields_are_same(known_tc_case.project_name, project_name) or
            not fields_are_same(known_tc_case.status, status) or
            not fields_are_same(known_tc_case.description, description)):
        known_tc_case.case_url = case_url
        known_tc_case.project_name = project_name
        known_tc_case.description = description
        known_tc_case.status = status
        known_tc_case.save()

        logger.info("**********************")
        logger.info(f"Updating a text change case ({str(known_tc_case)})")
        logger.info(f"case_number: {known_tc_case.case_number}")
        logger.info(f"project_name: {project_name}")
        logger.info("**********************")
        return True

    return False


def create_new_text_change(case_number, case_url, project_name, description, status):
    """Create a new text change case in the database.

    Args:
        case_number: Case number
        case_url: URL to case document
        project_name: Project name
        description: Case description
        status: Case status
    """
    logger.info("**********************")
    logger.info("Creating new text change case")
    logger.info(f"case_number: {case_number}")
    logger.info(f"project_name: {project_name}")
    logger.info("**********************")

    TextChangeCase.objects.create(
        case_number=case_number,
        case_url=case_url,
        project_name=project_name,
        description=description,
        status=status
    )


def upsert_text_change_case(data):
    """Create or update a text change case.

    Args:
        data: Dictionary with text change case data
    """
    known_tc_cases = TextChangeCase.objects.all()
    known_tc_case = determine_if_known_case(
        known_tc_cases,
        data["case_number"],
        data["project_name"]
    )

    if known_tc_case:
        update_text_change_if_changed(
            known_tc_case,
            data["case_url"],
            data["project_name"],
            data["description"],
            data["status"]
        )
    else:
        create_new_text_change(
            data["case_number"],
            data["case_url"],
            data["project_name"],
            data["description"],
            data["status"]
        )


def process_text_change_row(row):
    """Process a single text change case row.

    Args:
        row: BeautifulSoup tr element

    Returns:
        Dictionary with extracted data or None if validation fails
    """
    row_tds = row.find_all("td")
    data = extract_text_change_row_data(row_tds)

    if not validate_text_change_data(data):
        handle_text_change_validation_error(row_tds, data or {})
        return None

    # Check for "no active cases" sentinel
    if check_for_no_active_cases(data["case_number"]):
        return None

    # If no case URL, set to default
    if not data["case_url"]:
        data["case_url"] = "NA"

    return data


def text_changes_cases(page_content):
    """Process all text change cases from page content.

    Args:
        page_content: BeautifulSoup object with page HTML
    """
    if not page_content:
        return

    tc_tables = page_content.find_all("table")

    for tc_table in tc_tables[0]:
        table_thead = tc_table.find("thead")
        headers = validate_table_headers(table_thead)

        # Skip tables with invalid headers
        if not headers:
            continue

        tc_rows = get_rows_in_table(tc_table, "TCC")

        for tc in tc_rows:
            tc_data = process_text_change_row(tc)

            if tc_data:
                upsert_text_change_case(tc_data)


def extract_case_number_and_year(case_number_text):
    """Extract zpnum and zpyear from case number text.

    Args:
        case_number_text: Case number string (e.g., "Z-1234-23")

    Returns:
        Tuple of (zpnum, zpyear) as strings
    """
    parts = case_number_text.split("-")
    zpnum = parts[1]
    zpyear = "20" + parts[2][:2]

    return zpnum, zpyear


def extract_case_number_text(case_number_status_col):
    """Extract the case number text from the table cell.

    Handles complex HTML including links, SVGs, and multiple paragraphs.
    Extracts the first occurrence of a case number pattern (e.g., Z-1234-23).

    Args:
        case_number_status_col: BeautifulSoup td element

    Returns:
        Case number text string (e.g., "Z-1234-23")
    """
    import re

    full_text = case_number_status_col.get_text()

    # Pattern to match case numbers like Z-1234-23 or Z-13-25
    # Captures the first occurrence before any extra info like (TCZ-13-25)
    match = re.search(r'([A-Z]+-\d+-\d+)', full_text)

    if match:
        return match.group(1).strip()

    # Fallback to original logic if no pattern match found
    lines = full_text.split("\n")
    case_number_text = lines[0] if lines[0] else lines[1]

    return case_number_text.strip()


def extract_status(case_number_status_col, row_index, zoning_rows):
    """Extract status from case number cell or next row's first column.

    Handles complex HTML with links and SVGs by extracting text from paragraphs.
    Status is typically in the last paragraph of the cell.

    Args:
        case_number_status_col: BeautifulSoup td element
        row_index: Current row index
        zoning_rows: List of all zoning rows

    Returns:
        Status string
    """
    try:
        # Try to find paragraphs in the cell
        paragraphs = case_number_status_col.find_all("p")

        if paragraphs:
            # Status is typically in the last paragraph
            status = paragraphs[-1].get_text().strip()
            if status:
                return status

        # Fallback: split by newlines for simple cases
        lines = case_number_status_col.get_text().split("\n")
        status = lines[-1].strip() if lines[-1].strip() else lines[-2].strip()
        return status

    except (AttributeError, IndexError):
        # Status is on the next row
        next_row_status_col = zoning_rows[row_index + 1].find_all("td")[0]
        status = next_row_status_col.get_text().strip()
        return status


def validate_scraped_row(case_number_text, location, zoning_case, status):
    """Validate that all required fields were successfully scraped.

    Args:
        case_number_text: Case number text
        location: Project location
        zoning_case: Full zoning case identifier
        status: Case status

    Returns:
        Boolean indicating if row is valid
    """
    return bool(case_number_text and location and zoning_case and status)


def handle_validation_error(scraped_info, case_number_text, location, status, plan_url, location_url):
    """Log and send email notification for scraping errors.

    Args:
        scraped_info: List of scraped fields for debugging
        case_number_text: Case number text
        location: Project location
        status: Case status
        plan_url: URL to plan document
        location_url: URL to location
    """
    debug_info = [
        ["case_number_text", case_number_text],
        ["location", location],
        ["status", status],
        ["plan_url", plan_url],
        ["location_url", location_url]
    ]
    message = "scrape.zoning_requests: Problem scraping this row\n" + str(debug_info)
    logger.info(message)
    send_email_notice(message, email_admins())


def update_zoning_if_changed(known_zon, status, plan_url, location_url):
    """Update zoning record if any fields have changed.

    Args:
        known_zon: Zoning database object
        status: New status
        plan_url: New plan URL
        location_url: New location URL

    Returns:
        Boolean indicating if update occurred
    """
    if (not fields_are_same(known_zon.status, status) or
            not fields_are_same(known_zon.plan_url, plan_url) or
            not fields_are_same(known_zon.location_url, location_url)):

        old_status = known_zon.status
        old_plan_url = known_zon.plan_url
        old_location_url = known_zon.location_url

        known_zon.status = status
        known_zon.plan_url = plan_url
        known_zon.location_url = location_url
        known_zon.save()

        logger.info("**********************")
        logger.info("Updating a zoning request")
        logger.info(f"known_zon: {str(known_zon)}")

        if not fields_are_same(old_status, status):
            logger.info(f"Status: {old_status} → {status}")
        if not fields_are_same(old_plan_url, plan_url):
            logger.info(f"Plan URL: {old_plan_url} → {plan_url}")
        if not fields_are_same(old_location_url, location_url):
            logger.info(f"Location URL: {old_location_url} → {location_url}")

        logger.info("**********************")
        return True

    return False


def create_new_zoning(zpyear, zpnum, status, location, plan_url, location_url, zoning_case):
    """Create a new zoning request in the database.

    Args:
        zpyear: Zoning permit year
        zpnum: Zoning permit number
        status: Case status
        location: Project location
        plan_url: URL to plan document
        location_url: URL to location
        zoning_case: Full case identifier for logging
    """
    logger.info("**********************")
    logger.info("Creating new Zoning Request from web scrape")
    logger.info(f"case_number: {zoning_case}")
    logger.info(f"location: {location}")
    logger.info("**********************")

    Zoning.objects.create(
        zpyear=zpyear,
        zpnum=zpnum,
        status=status,
        location=location,
        plan_url=plan_url,
        location_url=location_url
    )


def process_zoning_row(row, index, zoning_rows):
    """Process a single zoning table row.
    ZON_EXPECTED = ["Case Number, Application & Status", "Location & Map Link", "Council District", "Staff Contact"]

    Args:
        row: BeautifulSoup tr element
        index: Row index in zoning_rows
        zoning_rows: List of all zoning rows

    Returns:
        Dictionary with extracted data or None if validation fails
    """
    zoning_row_tds = row.find_all("td")

    case_number_status_col = zoning_row_tds[0]
    project_name_location_col = zoning_row_tds[1]
    council_district_col = zoning_row_tds[2]

    # Skip if council district is empty
    if not council_district_col.get_text().strip():
        return None

    case_number_text = extract_case_number_text(case_number_status_col)
    status = extract_status(case_number_status_col, index, zoning_rows)
    plan_url = get_generic_link(case_number_status_col)

    location = re.sub(r"\s+", " ", project_name_location_col.get_text()).strip()
    location_url = get_generic_link(project_name_location_col)

    zoning_case = case_number_text.split("\n")[0]
    zpnum, zpyear = extract_case_number_and_year(zoning_case)

    # Check if case number format is invalid
    if zpnum is None or zpyear is None:
        debug_info = [
            ["case_number_text", case_number_text],
            ["zoning_case", zoning_case],
            ["location", location],
            ["status", status]
        ]
        message = "scrape.zoning_requests: Invalid case number format\n" + str(debug_info)
        logger.info(message)
        send_email_notice(message, email_admins())
        return None

    if not validate_scraped_row(case_number_text, location, zoning_case, status):
        handle_validation_error(None, case_number_text, location, status, plan_url, location_url)
        return None

    return {
        "zpyear": int(zpyear),
        "zpnum": int(zpnum),
        "status": status,
        "location": location,
        "plan_url": plan_url,
        "location_url": location_url,
        "zoning_case": zoning_case
    }


def upsert_zoning_request(zoning_data):
    """Create or update a zoning request.

    Args:
        zoning_data: Dictionary with zoning request data
    """
    existing = Zoning.objects.filter(
        zpnum=zoning_data["zpnum"],
        zpyear=zoning_data["zpyear"]
    ).first()

    if existing:
        update_zoning_if_changed(
            existing,
            zoning_data["status"],
            zoning_data["plan_url"],
            zoning_data["location_url"]
        )
    else:
        create_new_zoning(
            zoning_data["zpyear"],
            zoning_data["zpnum"],
            zoning_data["status"],
            zoning_data["location"],
            zoning_data["plan_url"],
            zoning_data["location_url"],
            zoning_data["zoning_case"]
        )


def zoning_requests(page_content):
    """Process all zoning requests from page content.

    Args:
        page_content: BeautifulSoup object with page HTML
    """
    if not page_content:
        return

    zoning_tables = page_content.find_all("table")

    for zoning_table in zoning_tables:
        zoning_rows = get_rows_in_table(zoning_table, "Zoning")

        for index, row in enumerate(zoning_rows):
            zoning_data = process_zoning_row(row, index, zoning_rows)

            if zoning_data:
                upsert_zoning_request(zoning_data)


def zoning_requests_old(page_content):
    if page_content:
        zoning_tables = page_content.find_all("table")

        for zoning_table in zoning_tables:
            zoning_rows = get_rows_in_table(zoning_table, "Zoning")

            for index, row in enumerate(zoning_rows):
                zoning_row_tds = row.find_all("td")

                # 4 columns
                case_number_status_col = zoning_row_tds[0]
                project_name_location_col = zoning_row_tds[1]
                council_district_col = zoning_row_tds[2]

                # If council_district_col is empty, let's skip this row
                if not council_district_col.get_text().strip():
                    continue

                # From case_number_status_col get
                #  * zpyear
                #  * zpnum
                #  * status
                #  * plan_url
                case_number_text = case_number_status_col.get_text().split("\n")[0]
                if not case_number_text:
                    # If they use a p tag inside the td, then we need the next item
                    case_number_text = case_number_status_col.get_text().split("\n")[1]
                if "mp" in case_number_text.lower():
                    case_number_text = case_number_text.lower().split("mp")[0]

                zoning_case = case_number_text.split("\n")[0]

                # Break up zoning_case
                scrape_num = zoning_case.split("-")[1]
                scrape_year = "20" + zoning_case.split("-")[2][:2]

                try:
                    status = case_number_status_col.get_text().split("\n")[-1].strip()
                    if status == "":
                        status = case_number_status_col.get_text().split("\n")[-2].strip()
                except AttributeError:
                    # case for when the status is on the second row
                    next_rows_status_col = zoning_rows[index + 1].find_all("td")[0]
                    status = next_rows_status_col.get_text().strip()

                plan_url = get_generic_link(case_number_status_col)

                # From project_name_location_col get location
                location = project_name_location_col.get_text().strip()
                location_url = get_generic_link(project_name_location_col)

                # If any of these variables are None, log it and move on.
                # Remarks come from the API
                # Status is from the web scrape
                if not case_number_text or not location or not zoning_case or not status:
                    scraped_info = [["zoning_row_tds", zoning_row_tds],
                                    ["case_number_text", case_number_text],
                                    ["location", location],
                                    ["location_url", location_url],
                                    ["status", status],
                                    ["plan_url", plan_url]]
                    message = "scrape.zoning_requests: Problem scraping this row"
                    message += str(scraped_info)
                    logger.info(message)
                    send_email_notice(message, email_admins())

                    continue

                # First check if we already have this zoning request
                if Zoning.objects.filter(zpnum=int(scrape_num), zpyear=int(scrape_year)).exists():
                    known_zon = Zoning.objects.get(zpyear=scrape_year, zpnum=scrape_num)

                    # If the status, plan_url, or location_url have changed, update the zoning request
                    if (not fields_are_same(known_zon.status, status) or
                            not fields_are_same(known_zon.plan_url, plan_url) or
                            not fields_are_same(known_zon.location_url, location_url)):
                        # A zoning web scrape only updates status and/or plan_url and/or location_url
                        known_zon.status = status
                        known_zon.plan_url = plan_url
                        known_zon.location_url = location_url

                        known_zon.save()

                        # Want to log what the difference is
                        difference = "*"
                        if not fields_are_same(known_zon.status, status):
                            difference += f"Difference: {str(known_zon.status)} changed to {str(status)}"
                        if not fields_are_same(known_zon.plan_url, plan_url):
                            difference += f"Difference: {str(known_zon.plan_url)} changed to {str(plan_url)}"
                        if not fields_are_same(known_zon.location_url, location_url):
                            difference += f"Difference: {str(known_zon.location_url)} changed to {str(location_url)}"

                        logger.info("**********************")
                        logger.info("Updating a zoning request")
                        logger.info(f"known_zon: {str(known_zon)}")
                        logger.info(difference)
                        logger.info("**********************")

                else:
                    # We don't know about it so create a new zoning request
                    logger.info("**********************")
                    logger.info("Creating new Zoning Request from web scrape")
                    logger.info(f"case_number: {zoning_case}")
                    logger.info(f"location: {location}")
                    logger.info("**********************")

                    Zoning.objects.create(zpyear=scrape_year,
                                          zpnum=scrape_num,
                                          status=status,
                                          location=location,
                                          plan_url=plan_url,
                                          location_url=location_url)


def extract_neighborhood_meeting_row_data(row_tds):
    """Extract all data fields from a neighborhood meeting row.
    NEIGHBOR_EXPECTED = [
            "Date & Time", "Meeting Location", "Site Location & Map",
            "Request", "Council District", "Applicant Contact", "Staff Contact"
        ]

    Args:
        row_tds: List of BeautifulSoup td elements from the row

    Returns:
        Dictionary with extracted data or None if extraction fails
    """
    if len(row_tds) < 4:
        return None

    meeting_datetime_details = get_generic_text(row_tds[0])
    meeting_location = get_generic_text(row_tds[1])
    rezoning_site_address = get_generic_text(row_tds[2])
    rezoning_site_address_url = get_generic_link(row_tds[2])
    rezoning_request = get_generic_text(row_tds[3])
    rezoning_request_url = get_generic_link(row_tds[3])

    return {
        "meeting_datetime_details": meeting_datetime_details,
        "meeting_location": meeting_location,
        "rezoning_site_address": rezoning_site_address,
        "rezoning_site_address_url": rezoning_site_address_url,
        "rezoning_request": rezoning_request,
        "rezoning_request_url": rezoning_request_url
    }


def apply_special_exceptions(data):
    """Apply special case exceptions for known data issues.

    Args:
        data: Dictionary with neighborhood meeting data

    Returns:
        Modified data dictionary
    """
    # Special case for BRT stations
    brt_text = "City-initiated rezoning of various properties located near planned Bus Rapid Transit (BRT) stations along New Bern Avenue"

    if data.get("rezoning_site_address") == brt_text:
        data["rezoning_site_address_url"] = "https://raleighnc.gov/planning/COR"

    return data


def validate_neighborhood_meeting_data(data):
    """Validate that all required fields are present.

    Args:
        data: Dictionary with neighborhood meeting data

    Returns:
        Boolean indicating if data is valid
    """
    if not data:
        return False

    required_fields = [
        "meeting_datetime_details",
        "rezoning_site_address_url",
        "meeting_location",
        "rezoning_site_address"
    ]

    return all(data.get(field) for field in required_fields)


def is_acknowledged_missing_data(rezoning_site_address):
    """Check if this is a known/acknowledged case with missing data.

    Args:
        rezoning_site_address: Address string

    Returns:
        Boolean indicating if this is an acknowledged exception
    """
    acknowledged = ["10854 Globe Rd"]
    return rezoning_site_address in acknowledged


def handle_neighborhood_meeting_validation_error(row_tds, data):
    """Log and send email notification for neighborhood meeting scraping errors.

    Args:
        row_tds: List of td elements
        data: Dictionary with extracted data
    """
    scraped_info = [
        ["meeting_datetime_details", data.get("meeting_datetime_details")],
        ["rezoning_site_address", data.get("rezoning_site_address")],
        ["rezoning_site_address_url", data.get("rezoning_site_address_url")],
        ["meeting_location", data.get("meeting_location")]
    ]
    message = "scrape.neighborhood_meetings: Problem scraping this row\n" + str(scraped_info)
    logger.info(message)
    send_email_notice(message, email_admins())


def update_neighborhood_meeting_if_changed(known_nm_case, data):
    """Update neighborhood meeting if any fields have changed.

    Args:
        known_nm_case: NeighborhoodMeeting database object
        data: Dictionary with new data

    Returns:
        Boolean indicating if update occurred
    """
    if (not fields_are_same(known_nm_case.meeting_datetime_details, data["meeting_datetime_details"]) or
            not fields_are_same(known_nm_case.rezoning_site_address, data["rezoning_site_address"]) or
            not fields_are_same(known_nm_case.rezoning_site_address_url, data["rezoning_site_address_url"]) or
            not fields_are_same(known_nm_case.meeting_location, data["meeting_location"]) or
            not fields_are_same(known_nm_case.rezoning_request, data["rezoning_request"]) or
            not fields_are_same(known_nm_case.rezoning_request_url, data["rezoning_request_url"])):
        known_nm_case.meeting_datetime_details = data["meeting_datetime_details"]
        known_nm_case.rezoning_site_address = data["rezoning_site_address"]
        known_nm_case.rezoning_site_address_url = data["rezoning_site_address_url"]
        known_nm_case.meeting_location = data["meeting_location"]
        known_nm_case.rezoning_request = data["rezoning_request"]
        known_nm_case.rezoning_request_url = data["rezoning_request_url"]
        known_nm_case.save()

        logger.info("**********************")
        logger.info(f"Updating a Neighborhood Meeting ({str(known_nm_case)})")
        logger.info(f"meeting_datetime_details: {data['meeting_datetime_details']}")
        logger.info(f"rezoning_site_address_url: {data['rezoning_site_address_url']}")
        logger.info("**********************")
        return True

    return False


def create_new_neighborhood_meeting(data):
    """Create a new neighborhood meeting in the database.

    Args:
        data: Dictionary with neighborhood meeting data
    """
    logger.info("**********************")
    logger.info("Creating new Neighborhood Meeting")
    logger.info(f"meeting_datetime_details: {data['meeting_datetime_details']}")
    logger.info(f"rezoning_site_address_url: {data['rezoning_site_address_url']}")
    logger.info("**********************")

    NeighborhoodMeeting.objects.create(
        meeting_datetime_details=data["meeting_datetime_details"],
        meeting_location=data["meeting_location"],
        rezoning_site_address=data["rezoning_site_address"],
        rezoning_site_address_url=data["rezoning_site_address_url"],
        rezoning_request=data["rezoning_request"],
        rezoning_request_url=data["rezoning_request_url"]
    )


def upsert_neighborhood_meeting(data):
    """Create or update a neighborhood meeting.

    Args:
        data: Dictionary with neighborhood meeting data
    """
    known_nm_cases = NeighborhoodMeeting.objects.all()
    known_nm_case = determine_if_known_case(
        known_nm_cases,
        data["meeting_datetime_details"],
        data["rezoning_site_address"]
    )

    if known_nm_case:
        update_neighborhood_meeting_if_changed(known_nm_case, data)
    else:
        create_new_neighborhood_meeting(data)


def process_neighborhood_meeting_row(row):
    """Process a single neighborhood meeting row.

    Args:
        row: BeautifulSoup tr element

    Returns:
        Dictionary with extracted data or None if validation fails
    """
    row_tds = row.find_all("td")
    data = extract_neighborhood_meeting_row_data(row_tds)

    if not data:
        return None

    # Apply any special case exceptions
    data = apply_special_exceptions(data)

    # Validate data
    if not validate_neighborhood_meeting_data(data):
        # Check if this is an acknowledged exception
        if not is_acknowledged_missing_data(data.get("rezoning_site_address")):
            handle_neighborhood_meeting_validation_error(row_tds, data)
        return None

    return data


def neighborhood_meetings(page_content):
    """Process all neighborhood meetings from page content.

    Args:
        page_content: BeautifulSoup object with page HTML
    """
    if not page_content:
        return

    nm_tables = page_content.find_all("table")

    for count, nm_table in enumerate(nm_tables):
        nm_rows = get_rows_in_table(nm_table, "NM")

        for nm_row in nm_rows:
            nm_data = process_neighborhood_meeting_row(nm_row)

            if nm_data:
                upsert_neighborhood_meeting(nm_data)


def design_alternate_cases(page_content):
    if page_content:
        dac_tables = page_content.find_all("table")

        for dac_table in dac_tables:
            dac_rows = get_rows_in_table(dac_table, "DAC")

            for dac_row in dac_rows:
                row_tds = dac_row.find_all("td")

                case_number = get_case_number_from_row(row_tds)
                if case_number != "No cases at this time.":
                    case_url = get_generic_link(row_tds[0])

                    project_name = get_generic_text(row_tds[1])
                    status = get_generic_text(row_tds[2])

                    # If any of these variables are None, log it and move on.
                    if not case_number or not case_url or not project_name or not status:
                        scraped_info = [["row_tds", row_tds],
                                        ["case_number", case_number],
                                        ["case_url", case_url],
                                        ["project_name", project_name],
                                        ["status", status]]
                        message = "scrape.design_alternate_cases: Problem scraping this row"
                        message += scraped_info
                        logger.info(message)
                        send_email_notice(message, email_admins())

                        continue

                    known_dac_cases = DesignAlternateCase.objects.all()
                    known_dac_case = determine_if_known_case(known_dac_cases, case_number, project_name)

                    if known_dac_case:
                        if (
                                not fields_are_same(known_dac_case.case_url, case_url) or
                                not fields_are_same(known_dac_case.project_name, project_name) or
                                not fields_are_same(known_dac_case.status, status)
                        ):
                            known_dac_case.case_url = case_url
                            known_dac_case.project_name = project_name
                            known_dac_case.status = status

                            known_dac_case.save()
                            logger.info("**********************")
                            logger.info("Updating a DA case (" + str(known_dac_case) + ")")
                            logger.info("scrape case_number:" + case_number)
                            logger.info("scrape project_name:" + project_name)
                            logger.info("**********************")

                    else:
                        logger.info("**********************")
                        logger.info("Creating new Design Alternate case")
                        logger.info("case_number:" + case_number)
                        logger.info("project_name:" + project_name)
                        logger.info("**********************")

                        DesignAlternateCase.objects.create(case_number=case_number,
                                                           case_url=case_url,
                                                           project_name=project_name,
                                                           status=status)
