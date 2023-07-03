import logging
import re
import requests
from datetime import datetime

from bs4 import BeautifulSoup
from django.conf import settings

from develop.models import *

logger = logging.getLogger("django")


def string_output_unix_datetime(unix_datetime):
    if unix_datetime:
        return datetime.fromtimestamp(unix_datetime / 1000).strftime("%Y-%m-%d %H:%M:%S")
    return str("None")


# def get_status_legend_dict():
    # legend has been removed on the city's page.
    # page_link = "https://www.raleighnc.gov/development"
    #
    # page_response = requests.get(page_link, timeout=10)
    #
    # if page_response.status_code == 200:
    #     page_content = BeautifulSoup(page_response.content, "html.parser")
    #
    #     # Status Abbreviations
    #     status_abbreviations_title = page_content.find("h2", text="Status Abbreviations")
    #     status_ul = status_abbreviations_title.findNext("ul")
    #     status_dict = {}
    #
    #     for li in status_ul.findAll("li"):
    #         status_dict[re.search("\(([^)]+)", li.get_text()).group(1)] = li.get_text()
    #
    #     return status_dict

    # It doesn't change much so if we can't get to the page for the legend, we'll use this static version.
    # return {"CC": "City Council (CC)",
    #         "EDI": "City Council Economic Development and Innovation Committee (EDI)",
    #         "GNR": "City Council Growth and Natural Resources Committee (GNR)",
    #         "HN": "City Council Healthy Neighborhoods Committee (HN)",
    #         "TTC": "City Council Transportation and Transit Committee (TTC)",
    #         "PC": "Planning Commission (PC)",
    #         "COW": "Planning Commission Committee of the Whole (COW)",
    #         "SPC": "Planning Commission Strategic Planning Committee (SPC)",
    #         "TCC": "Planning Commission Text Change Committee (TCC)",
    #         "UR": "Under Review (UR)",
    #         "PH": "Public Hearing (PH)",
    #         "APA": "Approved Pending Appeal (APA)",
    #         "CAPA": "Approved with Conditions Pending Appeal (CAPA)",
    #         "AP": "Appealed (AP)",
    #         "DPA": "Denied Pending Appeal (DPA)",
    #         "EPA": "Expired Pending Appeal (EPA)",
    #         "EFF": "Effective Date (EFF)",
    #         "BS": "Boundary Survey (BS)",
    #         "EX": "Exemption (EX)",
    #         "MI": "Miscellaneous (MI)",
    #         "R": "Recombination (R)",
    #         "RW": "Right-of-Way (RW)",
    #         "S": "Subdivision (S)",
    #         "SP": "Site Plan (SP)",
    #         "SR": "Site Review (SR)"}


# def get_status_text_abbrev(status):
#     # This will take in certain status abbreviations and return the whole text
#     # This only applies to web scraped items
#     status_dict = get_status_legend_dict()
#
#     try:
#         if "CAPA" in status:
#             status = status.replace("CAPA", status_dict["CAPA"])
#         elif status == "UR":
#             status = status.replace("UR", status_dict["UR"])
#         elif "GNR" in status:
#             status = status.replace("GNR", status_dict["GNR"])
#         elif "TCC" in status:
#             status = status.replace("TCC", status_dict["TCC"])
#         elif "CC" in status:
#             status = status.replace("CC", status_dict["CC"])
#         elif "PC" in status:
#             status = status.replace("PC", status_dict["PC"])
#         elif "PH" in status:
#             status = status.replace("PH", status_dict["PH"])
#     except TypeError:
#         n = datetime.now()
#         logger.info(n.strftime("%H:%M %m-%d-%y") + ": status is none")
#         return "Error Retrieving Status"
#
#     return status


def get_field_value(tracked_item, model_field):
    try:
        # If a date, convert to human readable
        if model_field.get_internal_type() == "BigIntegerField":
            return string_output_unix_datetime(getattr(tracked_item, model_field.name))
        # everything else, return as is
        else:
            return getattr(tracked_item, model_field.name)
    except AttributeError:
        n = datetime.now().strftime("%H:%M %m-%d-%y")
        logger.info(f"{n}: AttributeError - field is {str(model_field.name)} and item_most_recent = {str(tracked_item)}")


def difference_table_output(item):
    """This creates a table showing the previous and new values"""
    output = "### UPDATES\n"
    output += "||Previous|New|\n"
    output += "|---|---|---|\n"

    # Get the most recent version of the item and the one previously
    item_most_recent = item.history.first()
    item_previous = item_most_recent.prev_record

    # Get all the item fields
    fields = item._meta.get_fields()

    ignore_fields = ["created_date", "modified_date", "id", "EditDate", "updated"]

    # Loop through each field, except created_date, modified_date, and id.
    # If the fields are not equal, add it to output.
    for field in fields:
        if field.name not in ignore_fields:
            item_most_recent_field_value = get_field_value(item_most_recent, field)
            item_old_field_value = get_field_value(item_previous, field)

            # If there is a difference...
            if item_most_recent_field_value != item_old_field_value:
                output += f"|{field.verbose_name}|{str(item_old_field_value)}|{str(item_most_recent_field_value)}|\n"

    return output


def add_debug_text(item):
    """Additional text to help with debugging. Only add this if the instance is Develop"""
    # if settings.DEVELOP_INSTANCE == "Develop":
    #     try:
    #         text = f"[Develop - {item._meta.verbose_name.title()}]\n"
    #         return text
    #     except AttributeError:
    #         return ""
    # else:
    return ""


def get_submitted_year_text(item):
    try:
        return f"Submitted year: {str(item.submitted_field)}\n"
    except AttributeError:
        return ""


def get_plan_type_text(item):
    try:
        return f"Plan type: {str(item.plan_type)}\n"
    except AttributeError:
        return ""


def get_status_text(item):
    try:
        return f"Status: {str(item.status)}\n"
    except AttributeError:
        return ""


def get_major_street_text(item):
    try:
        return f"Major Street: {str(item.major_stre)}\n"
    except AttributeError:
        return ""


def get_item_url_text(item):
    if isinstance(item, DevelopmentPlan):
        try:
            return f"URL: {str(item.planurl)}\n\n"
        except AttributeError:
            return ""

    if isinstance(item, SiteReviewCase) or \
            isinstance(item, AdministrativeAlternate) or \
            isinstance(item, TextChangeCase):
        try:
            return f"URL: {str(item.case_url)}\n\n"
        except AttributeError:
            return ""

    if isinstance(item, Zoning):
        if item.plan_url:
            return f"Plan URL: {str(item.plan_url)}\n"
        else:
            return "Plan URL: NA\n"

    return ""


def get_updated_date_text(item):
    try:
        return f"Updated: {item.modified_date.strftime('%H:%M %b %d, %Y')}\n"
    except AttributeError:
        return ""


def get_location_text(item):
    try:
        return f"Location: {str(item.location)}\n"
    except AttributeError:
        return ""


def get_new_item_text(new_item):
    """Not including DevelopmentPlan as we don't scrape for them at this time."""
    if isinstance(new_item, Zoning):
        new_items_message = f"## {str(new_item.zpyear)}-{str(new_item.zpnum)}\n"
    elif isinstance(new_item, NeighborhoodMeeting):
        new_items_message = f"## {str(new_item.meeting_datetime_details)}\n"
        new_items_message += f"Rezoning Site Address: {new_item.rezoning_site_address}\n"
        new_items_message += f"Reoning Site Address URL: {new_item.rezoning_site_address_url}\n"
        new_items_message += f"Rezoning Request URL: {new_item.rezoning_request_url}\n"
        new_items_message += f"Meeting Location: {new_item.meeting_location}\n"
    else:
        new_items_message = f"## {str(new_item.project_name)}, {str(new_item.case_number)}\n"

    new_items_message += get_status_text(new_item)
    new_items_message += get_location_text(new_item)
    new_items_message += get_item_url_text(new_item)
    new_items_message += add_debug_text(new_item)

    return new_items_message


def get_updated_item_text(updated_item):
    """Not including DevelopmentPlan as we don't scrape for them at this time."""
    if isinstance(updated_item, Zoning):
        updated_items_message = f"## {str(updated_item.zpyear)}-{str(updated_item.zpnum)}\n"
    elif isinstance(updated_item, NeighborhoodMeeting):
        updated_items_message = f"## {str(updated_item.meeting_datetime_details)}\n"
        updated_items_message += f"Rezoning Site Address: {updated_item.rezoning_site_address}\n"
        updated_items_message += f"Reoning Site Address URL: {updated_item.rezoning_site_address_url}\n"
        updated_items_message += f"Rezoning Request URL: {updated_item.rezoning_request_url}\n"
        updated_items_message += f"Meeting Location: {updated_item.meeting_location}\n"
    else:
        updated_items_message = f"## {str(updated_item.project_name)}, {str(updated_item.case_number)}\n"

    updated_items_message += get_updated_date_text(updated_item)
    updated_items_message += get_status_text(updated_item)
    updated_items_message += get_location_text(updated_item)
    updated_items_message += get_item_url_text(updated_item)
    updated_items_message += difference_table_output(updated_item)
    updated_items_message += add_debug_text(updated_item)

    return updated_items_message
