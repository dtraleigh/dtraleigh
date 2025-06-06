import logging
import sys
from datetime import datetime

from develop.management.commands.actions import *
from develop.management.commands.location import *
from develop.models import *

logger = logging.getLogger("django")


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

        # Check if "features" exists in the response
        if not isinstance(devplan_data, dict) or "features" not in devplan_data:
            message = f"The 'features' key is missing from the API response: {devplan_data}"
            logger.error(message)
            send_email_notice(message, email_admins())
            return

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
                    known_dev_object.submitted_yr = attribute_data["submitted_yr"]
                    known_dev_object.approved = clean_unix_date(attribute_data["approved"])
                    # known_dev_object.daystoappr = attribute_data["daystoapprove"]
                    known_dev_object.plan_type = attribute_data["plan_type"]
                    known_dev_object.status = attribute_data["status"]
                    known_dev_object.appealperi = clean_unix_date(attribute_data["appealperiodends"])
                    known_dev_object.updated = clean_unix_date(attribute_data["updated"])
                    known_dev_object.sunset_dat = clean_unix_date(attribute_data["sunset_date"])
                    known_dev_object.acreage = attribute_data["acreage"]
                    known_dev_object.major_stre = attribute_data["major_street"]
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
                                                   major_stre=attribute_data["major_street"],
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
                    logger.info(e)
                    logger.info(attribute_data)
    except KeyError as e:
            message = f"Unexpected structure in the API response: {e}"
            logger.error(message)
            send_email_notice(message, email_admins())
    except Exception as e:
        message = f"An error occurred while processing the development plans: {e}"
        logger.exception(message)
        send_email_notice(message, email_admins())