import logging
import requests
import sys
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

            sr_page_link = "https://raleighnc.gov/permits/administrative-site-review-cases"
            # aad_page_link = "https://raleighnc.gov/SupportPages/administrative-alternate-design-cases"
            zon_page_link = "https://raleighnc.gov/planning/rezoning-cases"
            tc_page_link = "https://raleighnc.gov/planning/text-change-cases"
            neighbor_page_link = "https://raleighnc.gov/planning/neighborhood-meetings"
            # da_page_link = "https://raleighnc.gov/SupportPages/design-alternate-cases"

            zoning_requests(get_page_content(zon_page_link))
            # admin_alternates(get_page_content(aad_page_link))
            text_changes_cases(get_page_content(tc_page_link))
            site_reviews(get_page_content(sr_page_link))
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


# Deprecated after removing contact and contact_url
# def get_contact(content):
#     # content usually is a link but if not we need to account for a non-link piece of text
#     contact = content.find("a")
#
#     if contact:
#         return contact.get_text().strip()
#     else:
#         if content.text.strip() != "":
#             return content.text.strip()
#         return None


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
    """This is used to take a reliably straightforward piece of text."""
    try:
        return content.get_text().strip()
    except Exception as e:
        logger.info(e)
        return "None"

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
                    acked = ["No Case #", "ASR-0056-", "ASR-0075-2021"]
                    if case_number not in acked:
                        scraped_info = [["row_tds", row_tds],
                                        ["case_number", case_number],
                                        ["case_url", case_url],
                                        ["project_name", project_name],
                                        ["status", status]]
                        message = "scrape.site_reviews: Problem scraping this row"
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


def text_changes_cases(page_content):
    if page_content:
        tc_tables = page_content.find_all("table")

        for tc_table in tc_tables[:1]:
            # Only check the tables that have thead and td header
            # For some reason, this new table that we should skip has th header tags instead
            tcc_actual = []
            table_thead = tc_table.find("thead")
            thead_row = table_thead.find_all("td")

            for header in thead_row:
                tcc_actual.append(header.get_text().strip())

            if len(tcc_actual) > 0:
                tc_rows = get_rows_in_table(tc_table, "TCC")

                for tc in tc_rows:
                    row_tds = tc.find_all("td")

                    case_number = get_case_number_from_row(row_tds)
                    case_url = get_generic_link(row_tds[0])
                    project_name = get_generic_text(row_tds[1])
                    description = get_generic_text(row_tds[2])
                    status = get_generic_text(row_tds[3])

                    if case_number == "No active cases":
                        break

                    # Found a case where the TC name was not a link. We'll set it to something generic in the mean time.
                    if not case_url:
                        case_url = "NA"

                    # If any of these variables are None, log it and move on.
                    if not case_number or not case_url or not project_name or not status:
                        scraped_info = [["row_tds", row_tds],
                                        ["case_number", case_number],
                                        ["case_url", case_url],
                                        ["project_name", project_name],
                                        ["status", status]]
                        message = "scrape.text_changes_cases: Problem scraping this row"
                        message += str(scraped_info)
                        logger.info(message)
                        send_email_notice(message, email_admins())

                        continue

                    known_tc_cases = TextChangeCase.objects.all()
                    known_tc_case = determine_if_known_case(known_tc_cases, case_number, project_name)

                    # if known_tc_case was found, check for differences
                    # if known_tc_case was not found, then we assume a new one was added
                    # need to create
                    if known_tc_case:
                        # Check for difference between known_tc_case and the variables
                        # Assume that the tc_case number doesn't change.
                        if (
                                not fields_are_same(known_tc_case.case_url, case_url) or
                                not fields_are_same(known_tc_case.project_name, project_name) or
                                not fields_are_same(known_tc_case.status, status) or
                                not fields_are_same(known_tc_case.description, description)
                        ):
                            known_tc_case.case_url = case_url
                            known_tc_case.project_name = project_name
                            known_tc_case.description = description
                            known_tc_case.status = status

                            known_tc_case.save()
                            logger.info("**********************")
                            logger.info("Updating a text change case (" + str(known_tc_case) + ")")
                            logger.info("scrape case_number:" + case_number)
                            logger.info("scrape project_name:" + project_name)
                            logger.info("**********************")

                    else:
                        # create a new instance
                        logger.info("**********************")
                        logger.info("Creating new text change case")
                        logger.info("case_number:" + case_number)
                        logger.info("project_name:" + project_name)
                        logger.info("**********************")

                        TextChangeCase.objects.create(case_number=case_number,
                                                      case_url=case_url,
                                                      project_name=project_name,
                                                      description=description,
                                                      status=status)


def zoning_requests(page_content):
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


def neighborhood_meetings(page_content):
    if page_content:
        nm_tables = page_content.find_all("table")

        for count, nm_table in enumerate(nm_tables):
            # June 2, 22: Table within a table so skip the first one
            if count == 0:
                continue
            nm_rows = get_rows_in_table(nm_table, "NM")

            for row_count, nm_row in enumerate(nm_rows):
                row_tds = nm_row.find_all("td")

                meeting_datetime_details = get_generic_text(row_tds[0])
                meeting_location = get_generic_text(row_tds[1])
                rezoning_site_address = get_generic_text(row_tds[2])
                rezoning_site_address_url = get_generic_link(row_tds[2])
                rezoning_request = get_generic_text(row_tds[3])
                rezoning_request_url = get_generic_link(row_tds[3])

                # Need to clean up meeting_details, rezoning_request as it has new lines in it.
                meeting_datetime_details = meeting_datetime_details.replace("\n", "")
                meeting_datetime_details = meeting_datetime_details.replace("\t", "")
                rezoning_request = rezoning_request.replace("\n", "")
                rezoning_request = rezoning_request.replace("\t", "")

                # Special exceptions
                if rezoning_site_address == "City-initiated rezoning of various properties located near planned Bus " \
                                            "Rapid Transit (BRT) stations along New Bern Avenue":
                    rezoning_site_address_url = "https://raleighnc.gov/planning/COR"

                # If any of these variables are None, log it and move on.
                if not meeting_datetime_details or not rezoning_site_address_url or not meeting_location \
                        or not rezoning_site_address:
                    acked = ["10854 Globe Rd"]
                    if rezoning_site_address not in acked:
                        scraped_info = [["row_tds", row_tds],
                                        ["meeting_details", meeting_datetime_details],
                                        ["rezoning_site_address", rezoning_site_address],
                                        ["rezoning_site_address_url", rezoning_site_address_url],
                                        ["meeting_location", meeting_location]]
                        message = "scrape.neighborhood_meetings: Problem scraping this row\n"
                        message += str(scraped_info)
                        logger.info(message)
                        send_email_notice(message, email_admins())

                    continue

                known_nm_cases = NeighborhoodMeeting.objects.all()
                # See if we already know about this case from our records, else it's none (something new)
                known_nm_case = determine_if_known_case(known_nm_cases, meeting_datetime_details, rezoning_site_address)

                if known_nm_case:
                    if (
                            not fields_are_same(known_nm_case.meeting_datetime_details, meeting_datetime_details) or
                            not fields_are_same(known_nm_case.rezoning_site_address, rezoning_site_address) or
                            not fields_are_same(known_nm_case.rezoning_site_address_url, rezoning_site_address_url) or
                            not fields_are_same(known_nm_case.meeting_location, meeting_location) or
                            not fields_are_same(known_nm_case.rezoning_request, rezoning_request) or
                            not fields_are_same(known_nm_case.rezoning_request_url, rezoning_request_url)
                    ):
                        known_nm_case.meeting_datetime_details = meeting_datetime_details
                        known_nm_case.rezoning_site_address = rezoning_site_address
                        known_nm_case.rezoning_site_address_url = rezoning_site_address_url
                        known_nm_case.meeting_location = meeting_location
                        known_nm_case.rezoning_request = rezoning_request
                        known_nm_case.rezoning_request_url = rezoning_request_url

                        known_nm_case.save()
                        logger.info("**********************")
                        logger.info("Updating a Neighborhood Meeting (" + str(known_nm_case) + ")")
                        logger.info("scrape meeting_datetime_details:" + meeting_datetime_details)
                        logger.info("scrape rezoning_site_address_url:" + rezoning_site_address_url)
                        logger.info("**********************")
                else:
                    # create a new instance
                    logger.info("**********************")
                    logger.info("Creating new Neighborhood Meeting")
                    logger.info("meeting_datetime_details:" + meeting_datetime_details)
                    logger.info("rezoning_site_address_url:" + rezoning_site_address_url)
                    logger.info("**********************")

                    NeighborhoodMeeting.objects.create(meeting_datetime_details=meeting_datetime_details,
                                                       meeting_location=meeting_location,
                                                       rezoning_site_address=rezoning_site_address,
                                                       rezoning_site_address_url=rezoning_site_address_url,
                                                       rezoning_request=rezoning_request,
                                                       rezoning_request_url=rezoning_request_url)


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
