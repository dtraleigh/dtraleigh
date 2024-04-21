import sys
from datetime import datetime

from django.core.management.base import BaseCommand
from django.core.paginator import Paginator

from parcels.models import ParcelHistorical
from parcels.parcel_archive.functions import identify_coordinate_system, convert_geometry_to_epsg4326, \
    update_epsg4326_format, verify_epsg4326_format_is_correct


def convert_and_save_new_geojson(parcel, parcel_coordinate_system, verbose=False):
    if parcel_coordinate_system is None:
        print(f"Check {parcel}")
        print(parcel.data_geojson["geometry"])
        sys.exit(1)
    elif parcel_coordinate_system == "epsg:2264":
        if verbose:
            print(f"Checking {parcel} with epsg:2264 coordinates. Converting to epsg:4326 coordinates.")
        parcel.data_geojson["geometry"] = convert_geometry_to_epsg4326(parcel.data_geojson["geometry"])
        if verbose:
            print(f"{parcel} converted. Updating format if the coordinates need to be switched.")
        parcel.data_geojson["geometry"] = update_epsg4326_format(parcel)
        if verbose:
            print(f"{parcel} updated. Saving.")
        parcel.save()
    elif parcel_coordinate_system == "epsg:4326":
        if verbose:
            print(f"Checking {parcel} with epsg:4326 coordinates")
        if not verify_epsg4326_format_is_correct(parcel):
            if verbose:
                print(f"{parcel} failed epsg:4326 verify check. Updating... ")
            parcel.data_geojson["geometry"] = update_epsg4326_format(parcel)
            if verbose:
                print(f"{parcel} is updated. Now saving.")
            parcel.save()


def get_elapsed_time(start_time, end_time):
    time_difference = end_time - start_time
    seconds = time_difference.total_seconds()
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    remaining_seconds = int(seconds % 60)

    return f"{hours} hours, {minutes} minutes, {remaining_seconds} seconds"


class Command(BaseCommand):
    def add_arguments(self, parser):
        # parser.add_argument("-t", "--test", action="store_true", help="Run a test without making any changes.")
        pass

    def handle(self, *args, **options):
        start_time = datetime.now()
        # Set as needed
        parcel_subset = ParcelHistorical.objects.all()
        coordinate_systems_found = []
        parcels_not_valid = []

        paginator = Paginator(parcel_subset, 10000)

        print(f"{paginator.num_pages} pages with {paginator.count} parcels total.")
        print(f"Page: ", end=" ")

        for page_number in paginator.page_range:
            page = paginator.page(page_number)
            print(f"{page_number}", sep=" ", end=" ", flush=True)

            for parcel in page.object_list:
                parcel_coordinate_system = identify_coordinate_system(parcel)
                convert_and_save_new_geojson(parcel, parcel_coordinate_system)

                coordinate_systems_found.append(parcel_coordinate_system)
                coordinate_systems_found = list(set(coordinate_systems_found))
                if not verify_epsg4326_format_is_correct(parcel):
                    parcels_not_valid.append(parcel)

                if len(parcels_not_valid) > 10:
                    print("More than 10 invalid parcels. Quitting script.")
                    sys.exit(1)

        print(f"\nCoordinate Systems Found: {coordinate_systems_found}")
        print(f"Parcel not valid: {parcels_not_valid}")

        end_time = datetime.now()

        print(f"\nStart: {start_time}")
        print(f"End: {end_time}")
        print(f"Elapsed Time: {get_elapsed_time(start_time, end_time)}")
