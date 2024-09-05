import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from django.core.management.base import BaseCommand
from django.core.paginator import Paginator

from parcels.models import ParcelHistorical
from parcels.parcel_archive.functions import identify_coordinate_system_from_parcel, convert_geometry_to_epsg4326, \
    update_epsg4326_format_from_parcel, verify_epsg4326_format_is_correct_from_parcel, \
    update_epsg4326_format_from_geometry, verify_epsg4326_format_is_correct_from_data_geojson


# Tries to convert everything to epsg:4326
def convert_and_save_new_geojson_from_parcel(parcel, parcel_coordinate_system, verbose=False):
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
        parcel.data_geojson["geometry"] = update_epsg4326_format_from_parcel(parcel)
        if verbose:
            print(f"{parcel} updated. Saving.")
        parcel.save()
    elif parcel_coordinate_system == "epsg:4326":
        if verbose:
            print(f"Checking {parcel} with epsg:4326 coordinates")
        if not verify_epsg4326_format_is_correct_from_parcel(parcel):
            if verbose:
                print(f"{parcel} failed epsg:4326 verify check. Updating... ")
            parcel.data_geojson["geometry"] = update_epsg4326_format_from_parcel(parcel)
            if verbose:
                print(f"{parcel} is updated. Now saving.")
            parcel.save()


def precheck_and_convert_geometry(parcel, parcel_coordinate_system):
    geometry = parcel.data_geojson["geometry"]

    if parcel_coordinate_system == "epsg:2264":
        converted_geometry = convert_geometry_to_epsg4326(geometry)
        converted_geometry = update_epsg4326_format_from_geometry(converted_geometry)
        return converted_geometry
    elif parcel_coordinate_system == "epsg:4326":
        if not verify_epsg4326_format_is_correct_from_parcel(parcel):
            converted_geometry = update_epsg4326_format_from_geometry(geometry)
            return converted_geometry
        return geometry
    else:
        raise InvalidParcelError(f"Check {geometry}")


def get_elapsed_time(start_time, end_time):
    time_difference = end_time - start_time
    seconds = time_difference.total_seconds()
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    remaining_seconds = int(seconds % 60)

    return f"{hours} hours, {minutes} minutes, {remaining_seconds} seconds"


class InvalidParcelError(Exception):
    pass


class Command(BaseCommand):
    def add_arguments(self, parser):
        # parser.add_argument("-t", "--test", action="store_true", help="Run a test without making any changes.")
        pass

    def handle(self, *args, **options):
        start_time = datetime.now()

        parcel_subset = self.get_parcel_subset()
        coordinate_systems_found = self.process_parcels(parcel_subset)

        self.print_summary(coordinate_systems_found, start_time)

    def get_parcel_subset(self):
        return ParcelHistorical.objects.all()

    def process_parcels(self, parcel_subset):
        paginator = Paginator(parcel_subset, 10000)
        coordinate_systems_found = set()
        parcels_not_valid = []
        parcels_to_update = []

        print(f"{paginator.num_pages} pages with {paginator.count} parcels total.")
        print(f"Page: ", end=" ")

        for page_number in paginator.page_range:
            page = paginator.page(page_number)
            print(f"{datetime.now()}: Processing page {page_number}.")

            for parcel in page.object_list:
                self.process_single_parcel(parcel, coordinate_systems_found, parcels_not_valid)
                parcels_to_update.append(parcel)

                if len(parcels_not_valid) > 10:
                    raise InvalidParcelError(f"More than 10 invalid parcels. {parcels_not_valid}. Quitting script.")

            if parcels_to_update:
                print(f"{datetime.now()}: Bulk updating page {page_number} with {len(parcels_to_update)} objects.")
                ParcelHistorical.objects.bulk_update(parcels_to_update, ['data_geojson'])
                parcels_to_update = []

        return coordinate_systems_found

    def process_single_parcel(self, parcel, coordinate_systems_found, parcels_not_valid):
        parcel_coordinate_system = identify_coordinate_system_from_parcel(parcel)
        parcel.data_geojson["geometry"] = precheck_and_convert_geometry(parcel, parcel_coordinate_system)

        coordinate_systems_found.add(parcel_coordinate_system)
        if not verify_epsg4326_format_is_correct_from_parcel(parcel):
            parcels_not_valid.append(parcel)

    def print_summary(self, coordinate_systems_found, start_time):
        print(f"\nCoordinate Systems Found: {list(coordinate_systems_found)}")

        end_time = datetime.now()
        print(f"\nStart: {start_time}")
        print(f"End: {end_time}")
        print(f"Elapsed Time: {get_elapsed_time(start_time, end_time)}")
