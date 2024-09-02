# After running process_archive_zip_files, this command is used to remove parcels that are not in Raleigh.
# To-do: After this works, merge it into process_archive_zip_files to not create the parcel at all.
import sys
from datetime import datetime

from django.core.management.base import BaseCommand
from django.core.paginator import Paginator

from parcels.models import ParcelHistorical
from parcels.parcel_archive.functions import (parcel_has_CITY_value, parcel_has_PLAN_JURIS_value,
                                              get_list_of_all_possible_CITY_values,
                                              get_list_of_all_possible_PLAN_JURIS_values, queryset_iterator)


class Command(BaseCommand):
    def add_arguments(self, parser):
        # parser.add_argument("-t", "--test", action="store_true", help="Run a test without making any changes.")
        pass

    def handle(self, *args, **options):
        start_time = datetime.now()
        print(f"Start: {start_time}")
        # Set as needed
        parcel_subset = ParcelHistorical.objects.all()

        paginator = Paginator(parcel_subset, 10000)
        parcel_historical_ids_to_delete = []

        print(f"{datetime.now()}: {paginator.num_pages} pages with {paginator.count} parcels total.")
        print(f"Page: ", end=" ")

        all_CITY_values_found = []
        all_PLAN_JURIS_values_found = []
        for page_number in paginator.page_range:
            page = paginator.page(page_number)
            print(f"{page_number}", sep=" ", end=" ", flush=True)

            # Validate that the parcels can be filtered by checking a variety of methods
            for parcel in page.object_list:
                # Method 1: Parcel geojson contains a CITY field = 'RAL'
                # Method 2: Parcel geojson contains a PLAN_JURIS field = 'RA'
                if not parcel_has_CITY_value(parcel) and not parcel_has_PLAN_JURIS_value(parcel):
                    print(f"Check {parcel}: {parcel.data_geojson}")
                    sys.exit(1)
                if parcel_has_CITY_value(parcel) and parcel.data_geojson["properties"]["CITY"] != "RAL":
                    parcel_historical_ids_to_delete.append(parcel.id)
                elif parcel_has_PLAN_JURIS_value(parcel) and parcel.data_geojson["properties"]["PLAN_JURIS"] != "RA":
                    parcel_historical_ids_to_delete.append(parcel.id)

            all_CITY_values_found = all_CITY_values_found + get_list_of_all_possible_CITY_values(page.object_list)
            all_CITY_values_found = list(set(all_CITY_values_found))

            all_PLAN_JURIS_values_found = all_PLAN_JURIS_values_found + get_list_of_all_possible_PLAN_JURIS_values(page.object_list)
            all_PLAN_JURIS_values_found = list(set(all_PLAN_JURIS_values_found))

        print(f"\nall_CITY_values_found: {all_CITY_values_found}")
        print(f"all_PLAN_JURIS_values_found: {all_PLAN_JURIS_values_found}")

        print(f'{datetime.now()}: Deleting parcels where parcel.data_geojson["properties"]["CITY"] != "RAL" or '
              'parcel.data_geojson["properties"]["PLAN_JURIS"] != "RA"')
        parcels_to_delete = ParcelHistorical.objects.filter(id__in=parcel_historical_ids_to_delete)

        # if parcels_to_delete.exists():
        #     total_objects = parcels_to_delete.count()
        #     print(f"{datetime.now()}: Need to delete {total_objects} parcels.")
        #
        #     for count, obj in enumerate(queryset_iterator(parcels_to_delete), start=1):
        #         try:
        #             obj.delete()
        #             if count % 1000 == 0 or count == total_objects:
        #                 remaining = total_objects - count
        #                 print(f"{datetime.now()}: {count} objects deleted, {remaining} remaining...")
        #         except Exception as e:
        #             print(f"{datetime.now()}: Error deleting object {obj.pk}: {e}")
        # else:
        #     print("No objects to delete.")

        if parcels_to_delete.exists():
            total_objects = parcels_to_delete.count()
            print(f"{datetime.now()}: Need to delete {total_objects} parcels.")

            batch_size = 10000
            deleted_count = 0

            while deleted_count < total_objects:
                try:
                    # Fetch a batch of primary keys to delete
                    primary_keys = list(parcels_to_delete.values_list('pk', flat=True)[:batch_size])
                    if primary_keys:
                        # Perform raw delete
                        deleted = parcels_to_delete.filter(pk__in=primary_keys)._raw_delete(parcels_to_delete.db)
                        deleted_count += deleted

                        remaining = total_objects - deleted_count
                        print(f"{datetime.now()}: {deleted_count} objects deleted, {remaining} remaining...")
                    else:
                        break  # No more objects to delete
                except Exception as e:
                    print(f"{datetime.now()}: Error during raw deletion: {e}")
        else:
            print("No objects to delete.")

        print(f"After filter, subset is down to: {parcel_subset.count()}")
        print(f"Parcels in the DB: {ParcelHistorical.objects.count()}")

        print(f"Start: {start_time}")
        print(f"End: {datetime.now()}")
