# After running process_archive_zip_files, this command is used to remove parcels that are not in Raleigh.
# To-do: After this works, merge it into process_archive_zip_files to not create the parcel at all.
import sys

from django.core.management.base import BaseCommand

from parcels.models import ParcelHistorical
from parcels.parcel_archive.functions import parcel_has_CITY_value, get_list_of_all_possible_CITY_values


class Command(BaseCommand):
    def add_arguments(self, parser):
        # parser.add_argument("-t", "--test", action="store_true", help="Run a test without making any changes.")
        pass

    def handle(self, *args, **options):
        increment = 10000
        page = 0
        total_parcels = ParcelHistorical.objects.count()
        print(total_parcels)

        print(f"Page: ", " ")
        all_CITY_values_found = []
        while page < total_parcels:
            all_parcel_subset = ParcelHistorical.objects.all()[page:page+increment]
            print(f"{page}", sep=" ", end=" ", flush=True)

            # Validate that the parcels can be filtered by checking a variety of methods
            # Method 1: Parcel geojson contains a CITY field = RAL or some other similar indicator
            for loop_count, parcel in enumerate(all_parcel_subset):
                # Check that the parcel even has the field
                if not parcel_has_CITY_value(parcel):
                    print(f"Check {parcel}: {parcel.data_geosjon}")
                    sys.exit(1)
            page += increment
            all_CITY_values_found = all_CITY_values_found + get_list_of_all_possible_CITY_values(all_parcel_subset)
            all_CITY_values_found = list(set(all_CITY_values_found))

        print(all_CITY_values_found)
