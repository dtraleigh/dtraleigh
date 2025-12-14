import logging

import requests

from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from rpd.models import *
from rpd.functions import is_glenwood_south

logger = logging.getLogger("django")

"""
Notes. After scanning all incidents in downtown from beginning to today, we see:
Crime category
{
    'ASSAULT',
    'UNAUTHORIZED MOTOR VEHICLE USE',
    'VANDALISM',
    'ALL OTHER OFFENSES',
    'ROBBERY',
    'MV THEFT',
    'KIDNAPPING',
    'HUMAN TRAFFICKING',
    'DISORDERLY CONDUCT',
    'OBSCENE MATERIAL',
    'STOLEN PROPERTY',
    'HUMANE',
    'EXTORTION',
    'MURDER',
    'TRAFFIC',
    'FRAUD',
    'BURGLARY/RESIDENTIAL',
    'BURGLARY/COMMERCIAL',
    'PROSTITUTION',
    'SEX OFFENSES',
    'MISCELLANEOUS',
    'EMBEZZLEMENT',
    'WEAPONS VIOLATION',
    'DRUGS',
    'ARSON',
    'LARCENY',
    'LARCENY FROM MV',
    'DRUG VIOLATIONS',
    'BRIBERY',
    'LIQUOR LAW VIOLATIONS',
    'JUVENILE'
}

Crime type
{
    '',
    'CRIMES AGAINST SOCIETY',
    'NULL',
    'CRIMES AGAINST PERSONS',
    'CRIMES AGAINST PROPERTY'
}

"""


def get_downtown_incidents_for_month(year, month):
    """
    Returns the features list from the response for all incidents that have district = downtown
    :param year: int year value
    :param month: int month value
    :return: json data list from query response
    """
    url = (f"https://services.arcgis.com/v400IkDOw1ad7Yad/arcgis/rest/services/Police_Incidents/"
           f"FeatureServer/0/query?where=reported_year={str(year)}"
           f"and district='Downtown' and reported_month={str(month)}&outFields=*&outSR=4326&f=json")

    response = requests.request("GET", url, headers={}, data={})
    response_json = response.json()

    try:
        if response_json["exceededTransferLimit"]:
            print(f"Exceeded response limit for {year}, month {month}")
            logger.warning(f"Exceeded response limit for {year}, month {month}")
    except KeyError:
        pass

    if "features" not in response_json:
        error_msg = f"'features' key not found in response for {year}, month {month}"
        print(f"ERROR: {error_msg}")
        print(f"HTTP Status Code: {response.status_code}")
        print(f"Response content: {response.text}")
        print(f"Parsed JSON: {response_json}")

        logger.error(error_msg)
        logger.error(f"HTTP Status Code: {response.status_code}")
        logger.error(f"Response content: {response.text}")
        logger.error(f"Parsed JSON: {response_json}")

        return []

    return response_json["features"]


def save_incidents_to_db(incidents):
    new_downtown_incidents = []
    new_glenwood_south_incidents = []

    for incident in incidents:
        if not Incident.objects.filter(objectid=incident["attributes"]["OBJECTID"]).exists():
            attrs_dict = {}
            for key, value in Incident.incident_mapping.items():
                attrs_dict[key] = incident["attributes"][value]

            try:
                incident_location = Point(incident["geometry"]["x"], incident["geometry"]["y"])
            except KeyError:
                incident_location = None

            # Incident.objects.create(**attrs_dict, geom=incident_location)
            new_incident = Incident(**attrs_dict, geom=incident_location)
            new_incident.save()
            new_incident.is_glenwood_south = is_glenwood_south(new_incident)
            new_incident.save()
            new_downtown_incidents.append(new_incident)

            if new_incident.is_glenwood_south:
                new_glenwood_south_incidents.append(new_incident)

    return new_downtown_incidents, new_glenwood_south_incidents


class Command(BaseCommand):
    help = "Example: scan_incidents 2020 -m 1"

    def add_arguments(self, parser):
        # Required arguments
        parser.add_argument("scan_year", help="year to get all incidents")

        # Optional arguments
        parser.add_argument("-m", "--month", type=int, help="Optional month param")

    def handle(self, *args, **options):
        scan_year = options["scan_year"]
        scan_month = options["month"]

        if not scan_month:
            for month in range(1, 13):
                incidents = get_downtown_incidents_for_month(scan_year, month)
                save_incidents_to_db(incidents)
        else:
            incidents = get_downtown_incidents_for_month(scan_year, scan_month)
            save_incidents_to_db(incidents)
