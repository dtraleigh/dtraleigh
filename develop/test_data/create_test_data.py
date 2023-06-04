"""
When running tests, these are used to populate the test database. The JSON files are serialized exports
taken from the develop app itself. To refresh that data, see refresh_test_data.py
"""

from django.core import serializers

# Not using this right now
# def create_test_data_dev_plans():
#     # Creates 87 Dev plans that took place in 2020
#     with open("develop/test_data/test_data_DevelopmentPlans.json") as jsonfile:
#         for obj in serializers.deserialize("json", jsonfile):
#             obj.save()


def create_test_data_site_reviews():
    # Creates SRs pulled from test after Jan 1, 2021 to April 7, 2022
    with open("develop/test_data/test_data_SiteReviewCase.json") as jsonfile:
        for obj in serializers.deserialize("json", jsonfile):
            obj.save()


def create_test_data_zoning():
    # Creates Zons pulled from test after Jan 1, 2021 to April 7, 2022
    with open("develop/test_data/test_data_Zoning.json") as jsonfile:
        for obj in serializers.deserialize("json", jsonfile):
            obj.save()


def create_test_data_aads():
    # Creates AADs pulled from test after Jan 1, 2021 to April 7, 2022
    with open("develop/test_data/test_data_AdministrativeAlternate.json") as jsonfile:
        for obj in serializers.deserialize("json", jsonfile):
            obj.save()


def create_test_data_tccs():
    # Creates TCCs pulled from test after Jan 1, 2021 to April 7, 2022
    with open("develop/test_data/test_data_TextChangeCases.json") as jsonfile:
        for obj in serializers.deserialize("json", jsonfile):
            obj.save()
