import logging
import json
import requests
import pytz

from bs4 import BeautifulSoup
from datetime import datetime
from datetime import timedelta

from develop.management.commands.text_generates import *
from develop.models import *
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings

from develop.management.commands.emails import *

logger = logging.getLogger("django")


def get_api_json(url):
    response = None

    try:
        response = requests.get(url)
    except requests.exceptions.ChunkedEncodingError:
        n = datetime.now().strftime("%H:%M %m-%d-%y")
        logger.info(f"{n}: problem hitting the api. ({url})")

    if response.status_code == 200:
        return response.json()

    return response


def get_total_developments():
    # Example:
    # {
    #   "count":6250
    # }
    total_dev_count_query = ("https://services.arcgis.com/v400IkDOw1ad7Yad/arcgis/rest/services/Development_Plans"
                             "/FeatureServer/0/query?where=1%3D1&outFields=*&returnGeometry=false"
                             "&outSR=4326&f=json&returnCountOnly=true")

    json_count = get_api_json(total_dev_count_query)

    return json_count["count"]


def get_all_ids(url):
    # Example:
    # {
    #     "objectIdFieldName": "OBJECTID",
    #     "objectIds": [
    #         35811,
    #         35812,
    #           .....
    #         42081,
    #         42082
    #       ]
    # }

    json_object_ids = get_api_json(url)

    try:
        object_ids = str(len(json_object_ids["objectIds"]))
        print(f"Number of ids: {object_ids}")
        return json_object_ids["objectIds"]
    except KeyError:
        n = datetime.now().strftime("%H:%M %m-%d-%y")
        message = f"{n}: KeyError: 'objectIds'\n"
        message += f"actions.get_all_ids: KeyError with variable json_object_ids in get_all_ids()\n"
        message += str(json_object_ids)
        logger.info(message)
        send_email_notice(message, email_admins())
        return None


def fields_are_same(object_item, api_or_web_scrape_item):
    """Return True if the two objects are the same, False if not"""
    try:
        return object_item == api_or_web_scrape_item
    except Exception:
        n = datetime.datetime.now().strftime("%H:%M %m-%d-%y")
        logger.info(f"{n}: Error comparing object_item, {str(object_item)}, with json_item, {str(api_or_web_scrape_item)}")


def get_status_legend_text():
    page_link = "https://www.raleighnc.gov/development"

    page_response = requests.get(page_link, timeout=10)

    if page_response.status_code == 200:
        page_content = BeautifulSoup(page_response.content, "html.parser")

        # Status Abbreviations
        status_abbreviations_title = page_content.find("h3", {"id": "StatusAbbreviations"})

        status_section = status_abbreviations_title.findNext("div")

        status_ul = status_section.find("ul")
        status_legend = ""

        for li in status_ul.findAll("li"):
            status_legend += li.get_text() + "\n"

        return status_legend

    return "Unable to scrape the status legend."


def api_object_is_different(known_object, item_json):
    """Return False unless any of the individual field compare functions return True"""
    n = datetime.now().strftime("%H:%M %m-%d-%y")

    # Reducing the number of fields here in order to simplify the app.
    model_field_to_compare = ["status", "major_street", "plan_name", "zoning"]

    for field in model_field_to_compare:
        try:
            if not fields_are_same(str(getattr(known_object, field)),
                                   str(item_json[DevelopmentPlan.developmentplan_mapping[field]])):
                logger.info(f"{n}: Difference found with {str(field)} on Development {str(known_object)}")
                logger.info(f"Known_object: {str(getattr(known_object, field))}"
                            f" ({str(type(getattr(known_object, field)))}),  item_json[{field}]: "
                            f"{str(item_json[DevelopmentPlan.developmentplan_mapping[field]])}"
                            f" ({str(type(item_json[DevelopmentPlan.developmentplan_mapping[field]]))})")
                logger.info("\n")
                logger.info("known_object------------->")
                logger.info(known_object)
                logger.info("\nitem_json-------------->")
                logger.info(item_json)
                return True
        except KeyError as e:
            logger.info(e)
            logger.info(field)
            logger.info(item_json)

    # Returning false here basically means no difference was found
    return False


def create_new_discourse_post(subscriber, item):
    headers = {
        "Content-Type": "application/json",
        "Api-Key": subscriber.api_key,
        "Api-Username": subscriber.name,
        "Accept": "*/*",
        "Cache-Control": "no-cache",
        "Host": "community.dtraleigh.com",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "cache-control": "no-cache"
    }

    post_url = "https://community.dtraleigh.com/posts.json"
    get_url = f"https://community.dtraleigh.com/t/{str(subscriber.topic_id)}.json"

    response = requests.request("GET", get_url, headers=headers)
    r = response.json()

    try:
        slug = r["slug"]
    except KeyError as e:
        logger.info(e)
        logger.info(str(r))
        message = f"Check logs for issue getting slug: {e}"
        send_email_notice(message, email_admins())
        return
    topic_header_url = f"https://community.dtraleigh.com/t/{slug}/{str(subscriber.topic_id)}/1"
    message = ""

    # Create discourse message, dropping DevelopmentPlan since we don't scrape for it. Feb 2022
    if item.created_date > timezone.now() - timedelta(hours=1):
        message += f"### *New {item._meta.verbose_name.title()}*\n\n***\n"
        message += get_new_item_text(item)
    else:
        message = f"### *Existing {item._meta.verbose_name.title()} Update*\n\n***\n"
        message += get_updated_item_text(item)

    message += f"\n\nSee status abbreviations and sources at " \
               f"<a href=\"{topic_header_url}\">the topic's header</a>."

    # POST to Discourse
    post_payload = json.dumps({"topic_id": subscriber.topic_id,
                               "raw": message})

    requests.request("POST", post_url, data=post_payload, headers=headers)
