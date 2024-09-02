import sys
from datetime import datetime

from django.core.management.base import BaseCommand
from django.core.paginator import Paginator

from parcels.models import ParcelHistorical
from parcels.parcel_archive.functions import (get_list_of_all_possible_CITY_values,
                                              get_list_of_all_possible_PLAN_JURIS_values)


class Command(BaseCommand):
    def add_arguments(self, parser):
        # parser.add_argument("-t", "--test", action="store_true", help="Run a test without making any changes.")
        pass

    def handle(self, *args, **options):
        start_time = datetime.now()
        # Set as needed
        parcel_subset = ParcelHistorical.objects.all()

        paginator = Paginator(parcel_subset, 10000)

        print(f"{paginator.num_pages} pages with {paginator.count} parcels total.")
        print(f"Page: ", end=" ")

        all_CITY_values_found = []
        all_PLAN_JURIS_values_found = []
        for page_number in paginator.page_range:
            page = paginator.page(page_number)
            print(f"{page_number}", sep=" ", end=" ", flush=True)

            all_CITY_values_found = all_CITY_values_found + get_list_of_all_possible_CITY_values(page.object_list)
            all_CITY_values_found = list(set(all_CITY_values_found))

            all_PLAN_JURIS_values_found = all_PLAN_JURIS_values_found + get_list_of_all_possible_PLAN_JURIS_values(page.object_list)
            all_PLAN_JURIS_values_found = list(set(all_PLAN_JURIS_values_found))

        print(f"all_CITY_values_found: {all_CITY_values_found}")
        print(f"all_PLAN_JURIS_values_found: {all_PLAN_JURIS_values_found}")

        print(f"Parcels in the DB: {ParcelHistorical.objects.count()}")

        print(f"Start: {start_time}")
        print(f"End: {datetime.now()}")
