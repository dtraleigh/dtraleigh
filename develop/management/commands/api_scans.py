import logging
import sys
from datetime import datetime

from develop.management.commands.actions import *
from develop.management.commands.location import *
from develop.models import *

logger = logging.getLogger("django")


# OBJECTIDs whose create() failed this run, so the first failing payload can be
# logged in full and the rest kept to one line each.
_failed_creates = set()


# The attributes development_api_scan reads out of every feature. This is the
# written-down half of our contract with the Development Plans service:
# describe_contract_mismatch refuses to process a response missing any of them,
# and a test asserts this tuple still matches what the scan actually reads, so
# the two cannot drift apart. Undetected drift is how a stale "major_stre" name
# survived long enough to fill debug.txt with 16MB of retries in a day.
DEVELOPMENT_PLAN_ATTRIBUTES = (
    "OBJECTID",
    "submitted",
    "submitted_yr",
    "approved",
    "plan_type",
    "status",
    "appealperiodends",
    "updated",
    "sunset_date",
    "acreage",
    "major_street",
    "developer",
    "plan_name",
    "lots_req",
    "lots_apprv",
    "sq_ft_req",
    "units_apprv",
    "units_req",
    "zoning",
    "plan_number",
    "GlobalID",
    "missing_middle",
)


def describe_contract_mismatch(devplan_data):
    """Say how a response departs from what the scan expects, or "" if it does not.

    Checked before a single attribute is read, because the drift being guarded
    against is quiet. A renamed key raises nothing on the update path - it just
    makes that one field stop updating, and nothing says so for months.
    """
    if devplan_data is None:
        return ("The API returned nothing at all - the request failed before any JSON "
                "was parsed.")

    if not isinstance(devplan_data, dict):
        # get_api_json hands back the raw response object on a non-200.
        return (f"The API returned a {type(devplan_data).__name__} rather than a JSON "
                f"object: {str(devplan_data)[:500]}")

    if "error" in devplan_data:
        return f"The API returned an error payload: {devplan_data['error']}"

    if "features" not in devplan_data:
        return (f"The response has no 'features' key. Its top-level keys are: "
                f"{sorted(devplan_data)}")

    features = devplan_data["features"]

    if not isinstance(features, list):
        return f"'features' is a {type(features).__name__} rather than a list."

    if not features:
        return ("'features' came back empty. The query asks for every plan submitted in "
                "2022 or later, so no matches at all means the query or the dataset "
                "changed rather than that there is nothing to do.")

    # Counted per attribute rather than stopping at the first bad feature, so a
    # field the city dropped from only some records still reads as a contract
    # problem and the notice says how widespread it is.
    missing = {}

    for feature in features:
        if not isinstance(feature, dict) or not isinstance(feature.get("attributes"), dict):
            return f"A feature is not shaped like {{'attributes': {{...}}}}: {str(feature)[:500]}"

        for name in set(DEVELOPMENT_PLAN_ATTRIBUTES) - set(feature["attributes"]):
            missing[name] = missing.get(name, 0) + 1

    if missing:
        detail = ", ".join(f"{name} (absent from {str(count)} of {str(len(features))} features)"
                           for name, count in sorted(missing.items()))

        return f"The scan reads attributes the response does not carry: {detail}"

    return ""


def unknown_attributes(devplan_data):
    """Attributes the API now sends that the scan does not read."""
    seen = set()

    for feature in devplan_data["features"]:
        seen |= set(feature["attributes"])

    return sorted(seen - set(DEVELOPMENT_PLAN_ATTRIBUTES))


def report_contract_mismatch(mismatch, url):
    """Tell the admins what changed and where our side of the contract lives."""
    message = ("The Development Plans API is not shaped the way this scan expects, so "
               "no plans were processed on this run.\n\n"
               f"What is different:\n  {mismatch}\n\n"
               f"URL:\n  {url}\n\n"
               "Our side of the contract lives in three places that have to agree:\n"
               "  - DEVELOPMENT_PLAN_ATTRIBUTES in develop/management/commands/api_scans.py\n"
               "  - DevelopmentPlan.developmentplan_mapping in develop/models.py\n"
               "  - the field assignments in development_api_scan()\n\n"
               "Processing stopped rather than carrying on with the fields that still "
               "line up. A renamed key raises nothing on the update path - it quietly "
               "stops updating that one field - so continuing would bank wrong data and "
               "say nothing about it.\n")

    logger.error(message)
    send_email_notice(message, email_admins(),
                      subject="Develop: Development Plans API contract mismatch")


def clean_unix_date(unix_datetime):
    try:
        if unix_datetime > 1000000000:
            return datetime.utcfromtimestamp(unix_datetime / 1000)
        return None
    except TypeError:
        return None


def development_api_scan():
    """Development Planning API
    https://data-ral.opendata.arcgis.com/datasets/development-plans"""

    # All developments after 2022.
    url = "https://services.arcgis.com/v400IkDOw1ad7Yad/arcgis/rest/services/Development_Plans/FeatureServer/0/query?where=submitted_yr>=2022&outFields=*&outSR=4326&f=json"
    try:
        devplan_data = get_api_json(url)

        # Validate the shape before reading anything out of it.
        mismatch = describe_contract_mismatch(devplan_data)

        if mismatch:
            report_contract_mismatch(mismatch, url)
            return

        added = unknown_attributes(devplan_data)

        if added:
            # Deliberately not fatal, and deliberately not an email. A column we
            # do not read breaks nothing, halting over one would mean no plan
            # updates at all until someone edits code, and mailing about it would
            # repeat every hour until they did.
            logger.info(f"The Development Plans API now sends attributes the scan does "
                        f"not read: {added}")

        for dev_plan in devplan_data["features"]:
            attribute_data = dev_plan["attributes"]
            # Not all plans are given coordinates
            try:
                # geometry_data_given = dev_plan["geometry"]
                geometry_data_point = Point(dev_plan["geometry"]["x"], dev_plan["geometry"]["y"])
            except KeyError:
                geometry_data_point = None

            # Try to get the development from the DB and check if it needs to be updated.
            if DevelopmentPlan.objects.filter(objectid=attribute_data["OBJECTID"]).exists():
                known_dev_object = DevelopmentPlan.objects.get(objectid=attribute_data["OBJECTID"])

                # If the new object is not the same as the one in the DB, update it.
                # Enhancement oppurtunity here
                if api_object_is_different(known_dev_object, attribute_data):
                    known_dev_object.objectid = attribute_data["OBJECTID"]
                    # known_dev_object.devplan_id = attribute_data["devplan_id"]
                    known_dev_object.submitted = clean_unix_date(attribute_data["submitted"])
                    known_dev_object.submitted_field = attribute_data["submitted_yr"]
                    known_dev_object.approved = clean_unix_date(attribute_data["approved"])
                    # known_dev_object.daystoappr = attribute_data["daystoapprove"]
                    known_dev_object.plan_type = attribute_data["plan_type"]
                    known_dev_object.status = attribute_data["status"]
                    known_dev_object.appealperi = clean_unix_date(attribute_data["appealperiodends"])
                    known_dev_object.updated = clean_unix_date(attribute_data["updated"])
                    known_dev_object.sunset_dat = clean_unix_date(attribute_data["sunset_date"])
                    known_dev_object.acreage = attribute_data["acreage"]
                    known_dev_object.major_street = attribute_data["major_street"]
                    # known_dev_object.cac = attribute_data["cac"]
                    # known_dev_object.engineer = attribute_data["engineer"]
                    # known_dev_object.engineer_p = attribute_data["engineer_phone"]
                    known_dev_object.developer = attribute_data["developer"]
                    # known_dev_object.developer_field = attribute_data["developer_phone"]
                    known_dev_object.plan_name = attribute_data["plan_name"]
                    # known_dev_object.planurl = attribute_data["planurl"]
                    # known_dev_object.planurl_ap = attribute_data["planurl_approved"]
                    # known_dev_object.planner = attribute_data["planner"]
                    known_dev_object.lots_req = attribute_data["lots_req"]
                    # known_dev_object.lots_rec = attribute_data["lots_rec"]
                    known_dev_object.lots_apprv = attribute_data["lots_apprv"]
                    known_dev_object.sq_ft_req = attribute_data["sq_ft_req"]
                    known_dev_object.units_appr = attribute_data["units_apprv"]
                    known_dev_object.units_req = attribute_data["units_req"]
                    known_dev_object.zoning = attribute_data["zoning"]
                    known_dev_object.plan_numbe = attribute_data["plan_number"]
                    # known_dev_object.creationda = clean_unix_date(attribute_data["CreationDate"])
                    # known_dev_object.creator = attribute_data["Creator"]
                    # known_dev_object.editdate = clean_unix_date(attribute_data["EditDate"])
                    # known_dev_object.editor = attribute_data["Editor"]
                    known_dev_object.global_id = attribute_data["GlobalID"]
                    known_dev_object.missing_middle = attribute_data["missing_middle"]

                    if geometry_data_point:
                        known_dev_object.geom = geometry_data_point

                    known_dev_object.save()
                    logger.info(f"Updating {known_dev_object}")

            # If we don't know about it, we need to add it
            else:
                try:
                    DevelopmentPlan.objects.create(objectid=attribute_data["OBJECTID"],
                                                   # devplan_id=attribute_data["devplan_id"],
                                                   submitted=clean_unix_date(attribute_data["submitted"]),
                                                   submitted_field=attribute_data["submitted_yr"],
                                                   approved=clean_unix_date(attribute_data["approved"]),
                                                   # daystoappr=attribute_data["daystoapprove"],
                                                   plan_type=attribute_data["plan_type"],
                                                   status=attribute_data["status"],
                                                   appealperi=clean_unix_date(attribute_data["appealperiodends"]),
                                                   updated=clean_unix_date(attribute_data["updated"]),
                                                   sunset_dat=clean_unix_date(attribute_data["sunset_date"]),
                                                   acreage=attribute_data["acreage"],
                                                   major_street=attribute_data["major_street"],
                                                   # cac=attribute_data["cac"],
                                                   # engineer=attribute_data["engineer"],
                                                   # engineer_p=attribute_data["engineer_phone"],
                                                   developer=attribute_data["developer"],
                                                   # developer_field=attribute_data["developer_phone"],
                                                   plan_name=attribute_data["plan_name"],
                                                   # planurl=attribute_data["planurl"],
                                                   # planurl_ap=attribute_data["planurl_approved"],
                                                   # planner=attribute_data["planner"],
                                                   lots_req=attribute_data["lots_req"],
                                                   # lots_rec=attribute_data["lots_rec"],
                                                   lots_apprv=attribute_data["lots_apprv"],
                                                   sq_ft_req=attribute_data["sq_ft_req"],
                                                   units_appr=attribute_data["units_apprv"],
                                                   units_req=attribute_data["units_req"],
                                                   zoning=attribute_data["zoning"],
                                                   plan_numbe=attribute_data["plan_number"],
                                                   # creationda=clean_unix_date(attribute_data["CreationDate"]),
                                                   # creator=attribute_data["Creator"],
                                                   # editdate=clean_unix_date(attribute_data["EditDate"]),
                                                   # editor=attribute_data["Editor"],
                                                   global_id=attribute_data["GlobalID"],
                                                   missing_middle=attribute_data["missing_middle"],
                                                   geom=geometry_data_point)
                    logger.info(f"Creating new DevelopmentPlan, objectid: {attribute_data['OBJECTID']}")
                except Exception as e:
                    logger.warning(f"Could not create DevelopmentPlan for OBJECTID "
                                   f"{attribute_data.get('OBJECTID')}: {e}")

                    # The payload once, not every time. A create that fails on one
                    # bad field fails for every new plan and keeps failing every
                    # run - the row never lands, so it is unknown again next hour
                    # - which spells the whole API response into debug.txt hourly.
                    if not _failed_creates:
                        logger.warning(f"First failing payload was: {attribute_data}")

                    _failed_creates.add(attribute_data.get("OBJECTID"))
    except KeyError as e:
            message = f"Unexpected structure in the API response: {e}"
            logger.error(message)
            send_email_notice(message, email_admins())
    except Exception as e:
        message = f"An error occurred while processing the development plans: {e}"
        logger.exception(message)
        send_email_notice(message, email_admins())