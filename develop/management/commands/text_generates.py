import logging
import re
import requests
from datetime import datetime

from bs4 import BeautifulSoup
from django.conf import settings

from develop.models import *
from develop.normalize import values_are_equivalent

logger = logging.getLogger("django")


def string_output_unix_datetime(unix_datetime):
    if unix_datetime:
        return datetime.fromtimestamp(unix_datetime / 1000).strftime("%Y-%m-%d %H:%M:%S")
    return str("None")


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


def escape_table_cell(value):
    """Make a value safe to drop into a single markdown table cell.

    A pipe would open a new column and a newline would end the row, so a status
    containing either one silently breaks the whole table.
    """
    text = str(value).replace("|", "\\|")

    return " ".join(text.split("\n")).replace("\r", "").strip()


def get_difference_rows(item):
    """Return the [(label, previous, new)] rows worth reporting for an item.

    An empty list means there is nothing to announce - the caller should skip the
    post entirely rather than publish a bare UPDATES table.
    """
    # The two newest history records, rather than history.first().prev_record:
    # prev_record filters on history_date__lt, so two saves landing in the same
    # clock tick make it return None even though a previous record exists. The
    # manager's ordering ("-history_date", "-history_id") breaks that tie for us.
    recent_history = list(item.history.all()[:2])

    # Nothing to diff against - a brand new record, or history that has been
    # pruned. Reporting every field as "None -> value" is worse than saying
    # nothing, which is what the old swallowed AttributeError amounted to.
    if len(recent_history) < 2:
        return []

    item_most_recent, item_previous = recent_history

    ignore_fields = ["created_date", "modified_date", "id", "EditDate", "updated"]

    rows = []

    for field in item._meta.get_fields():
        if field.name in ignore_fields:
            continue

        new_value = get_field_value(item_most_recent, field)
        old_value = get_field_value(item_previous, field)

        # values_are_equivalent rather than != so a value the city merely
        # re-typed ("10/6/26" -> "10/06/26") is not reported as an update. The
        # scrape should have caught it first, but a manual admin edit - or a
        # history record written before that check existed - would not have been.
        if not values_are_equivalent(old_value, new_value):
            rows.append((field.verbose_name, old_value, new_value))

    return rows


def no_difference_reason(item):
    """Say why get_difference_rows came back empty, in words an admin can act on.

    The two empty cases have different causes and different fixes, so they are
    worth telling apart in the notice that goes out.
    """
    if item.history.count() < 2:
        return ("there is only one history record for it, so there is no previous "
                "version to compare against. That usually means the record was saved "
                "twice inside a single scrape, or that its history was pruned.")

    return ("every field that differs between the last two saved versions differs "
            "only in how it was typed, not in what it says, so the change was treated "
            "as not significant.")


def difference_table_output(item):
    """This creates a table showing the previous and new values"""
    rows = get_difference_rows(item)

    if not rows:
        return ""

    output = "### UPDATES\n"
    output += "||Previous|New|\n"
    output += "|---|---|---|\n"

    for label, old_value, new_value in rows:
        output += f"|{label}|{escape_table_cell(old_value)}|{escape_table_cell(new_value)}|\n"

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


def create_zoning_case_text(item):
    year_two_digits = str(item.zpyear)[-2:] if item.zpyear is not None else ""
    num = item.zpnum if item.zpnum is not None else ""
    return f"## Z-{num}-{year_two_digits}\n"


def get_new_item_text(new_item):
    """Not including DevelopmentPlan as we don't scrape for them at this time."""
    if isinstance(new_item, Zoning):
        new_items_message = create_zoning_case_text(new_item)
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
        updated_items_message = create_zoning_case_text(updated_item)
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
