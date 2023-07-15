import requests

from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from rpd.models import *

"""
Mar 28 - This returned:
{'North', 'Southeast', 'UNK', 'Northeast', 'Northwest', 'Southwest', 'Downtown'}
"""


def get_incidents_for_month(year, month):
    # url = f"https://services.arcgis.com/v400IkDOw1ad7Yad/arcgis/rest/services/Police_Incidents/FeatureServer/0/query?where=reported_year={str(year)} and district='Downtown' and reported_month={str(month)} and reported_block_address<>''&outFields=*&outSR=4326&f=json"
    url = f"https://services.arcgis.com/v400IkDOw1ad7Yad/arcgis/rest/services/Police_Incidents/FeatureServer/0/query?where=reported_year={str(year)} and reported_month={str(month)}&outFields=*&outSR=4326&f=json"

    response = requests.request("GET", url, headers={}, data={})
    response_json = response.json()

    return response_json["features"]


class Command(BaseCommand):
    def handle(self, *args, **options):
        districts_found_in_results = set([])
        target_years = [2015, 2016, 2017, 2018, 2019, 2020, 2021]

        for year in target_years:
            for month in range(1, 13):
                incidents_in_this_month = get_incidents_for_month(year, month)
                for incident in incidents_in_this_month:
                    districts_found_in_results.add(incident["attributes"]["district"])

        print(districts_found_in_results)


