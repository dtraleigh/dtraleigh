import logging
import random
import json
import requests
from curl_cffi import requests as curl_requests
import time
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
from develop.normalize import is_cosmetic_change, normalize_for_comparison, values_are_equivalent

logger = logging.getLogger("django")

# Raleigh's CMS (raleighnc.gov / www.raleighnc.gov) sits behind a Cloudflare
# managed challenge that rejects python-requests on the TLS handshake, so plain
# requests.get() returns 403 with a "Just a moment..." interstitial. curl_cffi
# replays a real Chrome TLS fingerprint, which clears the challenge.
#
# The User-Agent has to match the TLS fingerprint. A UA naming us as a bot while
# the handshake says Chrome is a contradiction, and Cloudflare scores that
# mismatch - plus the word "bot" itself, since we are not on their verified-bot
# list - as suspicious. That is very likely what kept us hovering at the
# challenge threshold. We still identify ourselves and give the city a way to
# reach us, just in headers that do not fight the fingerprint.
#
# Note: maps.raleighnc.gov (the ArcGIS endpoints in get_api_json) is NOT behind
# Cloudflare and still uses plain requests.
RALEIGH_IMPERSONATE = "chrome"
RALEIGH_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
# Not a standard header, but it is the one thing in the request that tells the
# city who we are now that the UA has to look like Chrome. Swap in a real
# mailbox here if you would rather they could email you directly.
RALEIGH_CONTACT_HEADERS = {
    "X-Contact": "https://dtraleigh.com - civic data scraper, hourly",
}
RALEIGH_TIMEOUT = 30

# Cloudflare scores each request on its own, so a challenge is usually cleared by
# simply asking again - but not within a few seconds. Spread the attempts over a
# couple of minutes; on an hourly cron that costs nothing and covers a much wider
# window than the original 15s.
RALEIGH_MAX_RETRIES = 3
RALEIGH_BACKOFF = 15

_raleigh_session = None

# Statuses worth a second attempt. A Cloudflare challenge (403) is frequently
# transient - it reflects a bot score that varies with the reputation of the
# shared host IP we go out on, so the same request often succeeds moments later.
# The 52x range is Cloudflare's "origin misbehaved" family.
RETRYABLE_STATUSES = (403, 429, 500, 502, 503, 504, 520, 521, 522, 523, 524)


def reset_raleigh_session():
    """Drop the cached session so the next call starts with fresh cookies."""
    global _raleigh_session

    _raleigh_session = None


def get_raleigh_session():
    """Return a shared session so Cloudflare's __cf_bm cookie is reused."""
    global _raleigh_session

    if _raleigh_session is None:
        _raleigh_session = curl_requests.Session(impersonate=RALEIGH_IMPERSONATE)
        _raleigh_session.headers.update({"User-Agent": RALEIGH_USER_AGENT})
        _raleigh_session.headers.update(RALEIGH_CONTACT_HEADERS)

    return _raleigh_session


def describe_cf_response(response):
    """Summarize Cloudflare's diagnostic headers for logs and alert emails.

    CF-RAY is the identifier Cloudflare (or the city's IT staff) needs to look
    up why a specific request was challenged, so it is worth capturing. Its
    suffix is also the Cloudflare PoP that served us, which is worth comparing
    between successes and failures.
    """
    if response is None:
        return "no response"

    parts = [f"status={response.status_code}"]

    for header in ("cf-ray", "cf-cache-status", "cf-mitigated"):
        value = response.headers.get(header)

        if value:
            parts.append(f"{header}={value}")

    return ", ".join(parts)


def fetch_raleigh_page(page_link, timeout=RALEIGH_TIMEOUT, max_retries=RALEIGH_MAX_RETRIES):
    """Fetch a raleighnc.gov page past Cloudflare's managed challenge.

    Retries transient failures with a jittered backoff, starting a new session
    each time so the retry is not carrying a poisoned challenge cookie.

    Returns a response object exposing .status_code and .content, so callers can
    keep the same checks they used with requests.get(). If every attempt raised,
    the last exception is re-raised for the caller to report.
    """
    last_error = None

    for attempt in range(max_retries + 1):
        response = None

        try:
            response = get_raleigh_session().get(page_link, timeout=timeout)

            if response.status_code not in RETRYABLE_STATUSES:
                # Log the successes too: without them the alert emails are a
                # sample of failures only, and there is no way to tell whether
                # the failures cluster on a PoP, a cache miss, or a time of day.
                logger.info(
                    f"fetched {page_link} on attempt {attempt + 1} "
                    f"({describe_cf_response(response)})"
                )

                return response

        except Exception as e:
            last_error = e

        n = datetime.now().strftime("%H:%M %m-%d-%y")
        detail = describe_cf_response(response) if response is not None else f"error={last_error}"

        if attempt >= max_retries:
            logger.warning(f"{n}: giving up on {page_link} after {attempt + 1} attempts ({detail})")

            if response is not None:
                return response

            raise last_error

        backoff = RALEIGH_BACKOFF * (2 ** attempt) + random.uniform(0, 2)
        logger.warning(
            f"{n}: retrying {page_link} in {backoff:.1f}s "
            f"(attempt {attempt + 1}/{max_retries}) ({detail})"
        )

        # A fresh session picks up a new __cf_bm cookie rather than replaying
        # whatever state got us challenged.
        reset_raleigh_session()
        time.sleep(backoff)


def is_throttle_response(data):
    """ArcGIS returns rate-limit errors with HTTP 200 and an error body like:
    {'error': {'code': 429, 'message': 'Unable to perform query. Too many requests.',
               'details': ['API calls quota exceeded ... Retry after 60 sec.']}}
    Return the error dict if this is a 429 throttle, else None."""
    if isinstance(data, dict) and isinstance(data.get("error"), dict):
        if data["error"].get("code") == 429:
            return data["error"]
    return None


def get_api_json(url, max_retries=3, default_backoff=60):
    """Hit an API and return the parsed JSON.

    Handles ArcGIS rate limiting (HTTP 429, or a 200 response whose body is a
    429 error) by backing off and retrying up to max_retries times.
    """
    for attempt in range(max_retries + 1):
        response = None

        try:
            response = requests.get(url)
        except requests.exceptions.ChunkedEncodingError:
            n = datetime.now().strftime("%H:%M %m-%d-%y")
            logger.info(f"{n}: problem hitting the api. ({url})")
            return response

        if response.status_code == 200:
            data = response.json()

            throttle = is_throttle_response(data)
            if throttle is None:
                return data
        elif response.status_code == 429:
            throttle = {"details": [response.text]}
        else:
            return response

        # We were throttled. Back off and retry unless we're out of attempts.
        if attempt >= max_retries:
            n = datetime.now().strftime("%H:%M %m-%d-%y")
            logger.warning(f"{n}: API throttled and out of retries. ({url}) {throttle}")
            return data if response.status_code == 200 else response

        backoff = default_backoff
        n = datetime.now().strftime("%H:%M %m-%d-%y")
        logger.warning(
            f"{n}: API throttled, backing off {backoff}s "
            f"(attempt {attempt + 1}/{max_retries}). ({url})"
        )
        time.sleep(backoff)


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
    """Return True if the two values mean the same thing, False if not.

    Values that differ only in how they were typed count as the same - see
    develop/normalize.py. Two consequences worth knowing: a date the city
    re-spelled ("10/6/26" -> "10/06/26") no longer counts as a change, and None
    and "" now compare equal, which ends the null-versus-empty-string churn.
    """
    return values_are_equivalent(object_item, api_or_web_scrape_item)


# Updates this run decided not to announce, drained into one digest email at the
# end of the command rather than mailed one at a time. If the city ever reformats
# its whole table at once - a CMS change re-rendering every status - that is one
# email instead of one per case.
#
# Module-level state in the same vein as _raleigh_session above, and safe for the
# same reason: the only callers are management commands, one run per process.
_skipped_updates = []


def reset_skipped_updates():
    """Start a run with an empty collector."""
    global _skipped_updates

    _skipped_updates = []


def record_skipped_update(item, reason, detail=""):
    """Note that an item changed but no Discourse post was made.

    Nothing is sent here - send_skipped_update_digest() mails the lot at the end
    of the run.
    """
    _skipped_updates.append((f"{item._meta.verbose_name} '{str(item)}'", reason, detail))


def describe_cosmetic_changes(changes):
    """Spell out the value pairs that were judged equivalent.

    Values are repr'd so an admin can see whitespace and &nbsp; for what they
    are, and each pair is shown next to the canonical form both reduce to -
    that form is the evidence for the call we made.
    """
    detail = ""

    for name, (old_value, new_value) in changes.items():
        detail += f"  Field: {name}\n"
        detail += f"    Previous:       {repr(old_value)}\n"
        detail += f"    New:            {repr(new_value)}\n"
        detail += f"    Both reduce to: {repr(normalize_for_comparison(new_value))}\n"

    detail += ("\n  The new value was saved so our copy matches the city, but "
               "modified_date\n  and the history record were left alone.\n")

    return detail


def send_skipped_update_digest():
    """Mail the admins one summary of everything this run chose not to announce.

    Kept non-fatal on purpose. send_email_notice uses fail_silently=False, and
    this runs at the end of a scrape that otherwise worked - an SMTP outage must
    not turn a healthy run into a failed one.
    """
    skipped = list(_skipped_updates)
    reset_skipped_updates()

    if not skipped:
        return

    count = len(skipped)
    plural = "update" if count == 1 else "updates"
    verb = "was" if count == 1 else "were"

    message = f"{str(count)} {plural} {verb} not posted to Discourse during this run.\n"

    # Grouped by reason rather than listed flat: a table-wide reformat gives every
    # entry the same reason, and repeating that paragraph twenty times buries the
    # part that actually differs between them.
    by_reason = {}

    for label, reason, detail in skipped:
        by_reason.setdefault(reason, []).append((label, detail))

    for reason, entries in by_reason.items():
        message += f"\nReason: {reason}\n"

        for label, detail in entries:
            message += f"\n{'-' * 68}\n"
            message += f"{label}\n"

            if detail:
                message += f"\n{detail}"

    message += f"\n{'-' * 68}\n"
    message += ("The rules that decide what counts as a significant change are in\n"
                "develop/normalize.py.\n")

    try:
        send_email_notice(
            message,
            email_admins(),
            subject=f"Develop: {str(count)} {plural} skipped (no significant change)",
        )
    except Exception as e:
        logger.info(f"Could not email the skipped-update digest: {str(e)}")


def sync_cosmetic_values(instance, **new_values):
    """Persist re-typed-but-equivalent values without announcing them.

    A queryset .update() skips save(), so simple-history writes no record and
    modified_date (auto_now) is left alone - which is what keeps notify, who
    works off modified_date, from treating a re-typing as news. Our copy still
    tracks whatever the city is currently publishing.

    Returns the fields it synced, so callers can log them.
    """
    # The old values are captured before anything is written, so the notice to
    # the admins can show the pair that were judged equivalent.
    changes = {}

    for name, value in new_values.items():
        old_value = getattr(instance, name)

        if is_cosmetic_change(old_value, value):
            changes[name] = (old_value, value)

    if not changes:
        return {}

    cosmetic = {name: new_value for name, (old_value, new_value) in changes.items()}

    type(instance).objects.filter(pk=instance.pk).update(**cosmetic)

    # .update() leaves the in-memory instance alone, so mirror the values onto it.
    for name, value in cosmetic.items():
        setattr(instance, name, value)

    logger.info(f"Cosmetic-only change on {instance._meta.verbose_name} "
                f"({str(instance)}), synced without notifying: {cosmetic}")

    record_skipped_update(
        instance,
        "the only differences found were in how the value was typed, not in what "
        "it says, so the change was treated as not significant.",
        describe_cosmetic_changes(changes),
    )

    return cosmetic


def get_status_legend_text():
    page_link = "https://www.raleighnc.gov/development"

    page_response = fetch_raleigh_page(page_link)

    if page_response.status_code == 200:
        page_content = BeautifulSoup(page_response.content, "html.parser")

        # Status Abbreviations
        # As of 08-2026 this heading is no longer on the page; guard rather than
        # raising AttributeError on the chained lookups below.
        status_abbreviations_title = page_content.find("h3", {"id": "StatusAbbreviations"})

        if not status_abbreviations_title:
            return "Unable to scrape the status legend."

        status_section = status_abbreviations_title.findNext("div")
        status_ul = status_section.find("ul") if status_section else None

        if not status_ul:
            return "Unable to scrape the status legend."

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
        # Nothing field-level to report means there is nothing to say. Posting an
        # empty UPDATES table just trains readers to ignore us. The scrape should
        # already have skipped a re-typed value, so this is the backstop.
        if not get_difference_rows(item):
            logger.info(f"No reportable changes on {item._meta.verbose_name} "
                        f"{str(item)}, skipping the Discourse post.")
            record_skipped_update(item, no_difference_reason(item))
            return

        message = f"### *Existing {item._meta.verbose_name.title()} Update*\n\n***\n"
        message += get_updated_item_text(item)

    message += f"\n\nSee status abbreviations and sources at " \
               f"<a href=\"{topic_header_url}\">the topic's header</a>."

    # POST to Discourse
    post_payload = json.dumps({"topic_id": subscriber.topic_id,
                               "raw": message})

    requests.request("POST", post_url, data=post_payload, headers=headers)

def ensure_correct_discourse_title(subscriber):
    expected_title = "Raleigh-area Mall / Life-Style Center / RTP Redevelopments"

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

    topic_id = 1184
    get_url = f"https://community.dtraleigh.com/t/{topic_id}.json"
    response = requests.get(get_url, headers=headers)

    if response.status_code != 200:
        logger.error(f"Failed to fetch topic. Status code: {response.status_code}, Response: {response.text}")
        return

    topic_data = response.json()
    current_title = topic_data.get("title")

    if current_title != expected_title:
        logger.info(f"Title mismatch. Updating topic title from '{current_title}' to '{expected_title}'")

        update_url = f"https://community.dtraleigh.com/t/-/{topic_id}.json"
        update_payload = json.dumps({"title": expected_title})

        update_response = requests.put(update_url, data=update_payload, headers=headers)

        if update_response.status_code == 200:
            logger.info("Topic title successfully updated.")
        else:
            logger.error(f"Failed to update topic title. Status code: {update_response.status_code}, Response: {update_response.text}")
    else:
        logger.info("Topic title is already correct.")