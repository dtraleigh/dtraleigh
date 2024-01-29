# After running process_archive_zip_files, this command is used to remove parcels that are not in Raleigh.
# To-do: After this works, merge it into process_archive_zip_files to not create the parcel at all.
import sys

from django.core.management.base import BaseCommand
from django.core.paginator import Paginator

from parcels.models import ParcelHistorical
from parcels.parcel_archive.functions import parcel_has_CITY_value, get_list_of_all_possible_CITY_values


class Command(BaseCommand):
    def add_arguments(self, parser):
        # parser.add_argument("-t", "--test", action="store_true", help="Run a test without making any changes.")
        pass

    def handle(self, *args, **options):
        paginator = Paginator(ParcelHistorical.objects.all(), 10000)
        parcel_historical_ids_to_delete = []

        print(f"{paginator.num_pages} pages with {paginator.count} parcels total.")
        print(f"Page: ", end=" ")

        all_CITY_values_found = []
        for page_number in paginator.page_range:
            page = paginator.page(page_number)
            print(f"{page_number}", sep=" ", end=" ", flush=True)

            # Validate that the parcels can be filtered by checking a variety of methods
            # Method 1: Parcel geojson contains a CITY field = RAL or some other similar indicator
            for parcel in page.object_list:
                # Check that the parcel even has the field
                if not parcel_has_CITY_value(parcel):
                    print(f"Check {parcel}: {parcel.data_geojson}")
                    sys.exit(1)
                if parcel.data_geojson["properties"]["CITY"] != "RAL":
                    parcel_historical_ids_to_delete.append(parcel.id)
                    print(parcel)
                    sys.exit(1)

            all_CITY_values_found = all_CITY_values_found + get_list_of_all_possible_CITY_values(page.object_list)
            all_CITY_values_found = list(set(all_CITY_values_found))

        print(f"all_CITY_values_found: {all_CITY_values_found}")

        print('Deleting parcels where parcel.data_geojson["properties"]["CITY"] != "RAL"')
        ParcelHistorical.objects.filter(id__in=parcel_historical_ids_to_delete).delete()

        print(f"Parcels left: {ParcelHistorical.objects.count()}")
