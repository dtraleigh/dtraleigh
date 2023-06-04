from django.core.management.base import BaseCommand
from develop.models import *
from django.core import serializers
from develop.models import *
import datetime


class Command(BaseCommand):
    def handle(self, *args, **options):
        JSONSerializer = serializers.get_serializer("json")
        json_serializer = JSONSerializer()

        # Export site review data to test_data_SiteReviewCase.json
        SRs = SiteReviewCase.objects.filter(created_date__gte=datetime.date(2021, 1, 1))
        with open("develop/test_data/test_data_SiteReviewCase.json", "w+") as out:
            json_serializer.serialize(SRs, stream=out)

        # Export admin alternate data to test_data_AdministrativeAlternate.json
        AADs = AdministrativeAlternate.objects.filter(created_date__gte=datetime.date(2021, 1, 1))
        with open("develop/test_data/test_data_AdministrativeAlternate.json", "w+") as out:
            json_serializer.serialize(AADs, stream=out)

        # Export text change data to test_data_TextChangeCases.json
        TCCs = TextChangeCase.objects.filter(created_date__gte=datetime.date(2021, 1, 1))
        with open("develop/test_data/test_data_TextChangeCases.json", "w+") as out:
            json_serializer.serialize(TCCs, stream=out)

        # Export zoning data to test_data_Zoning.json
        zons = Zoning.objects.filter(created_date__gte=datetime.date(2021, 1, 1))
        with open("develop/test_data/test_data_Zoning.json", "w+") as out:
            json_serializer.serialize(zons, stream=out)
