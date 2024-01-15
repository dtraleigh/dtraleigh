from django.core.management.base import BaseCommand

from datetime import datetime
from prettytable import PrettyTable

from parcels.models import Snapshot, ParcelHistorical
from parcels.parcel_archive.ZipFile import ZipFile
from parcels.parcel_archive.DataSnapshot import DataSnapshot

from parcels.parcel_archive.functions import (get_zip_files_list, get_parcel_data_dirs,
                                              get_list_of_features_from_geojson_file)


class Command(BaseCommand):

    def add_arguments(self, parser):
        # parser.add_argument("-t", "--test", action="store_true", help="Run a test without making any changes.")
        pass

    def handle(self, *args, **options):
        start_time = datetime.now()

        results_table = PrettyTable()
        results_table.field_names = ["Snapshot", "shp file"]

        zip_files = get_zip_files_list()
        zip_file_objects = [ZipFile(zip_file) for zip_file in zip_files]

        for zip_file_object in zip_file_objects:
            zip_file_object.unzip_the_file()

        data_dirs = get_parcel_data_dirs()
        data_snapshots = []
        for data_dir in data_dirs:
            data_snapshot = DataSnapshot(f"{data_dir}")
            data_snapshots.append(data_snapshot)
            results_table.add_row([data_snapshot.directory_path_and_name, data_snapshot.get_shp_data_file])

        print(results_table)

        for data_snapshot in data_snapshots:
            output = data_snapshot.extract_geojson_from_shp()
            print(output)

        # Go through each snapshot
        print("Going through each geojson file now and creating features.")
        for data_snapshot in data_snapshots:
            if not Snapshot.objects.filter(name=data_snapshot.directory_name).exists():
                new_snapshot = Snapshot(name=data_snapshot.directory_name)
                new_snapshot.save()
                print(f"Created new snapshot, {new_snapshot}")
            else:
                print(f"Skipping {data_snapshot.directory_name} as it already exists in the DB.")
                continue

            print("Getting list of features from the geojson file.")
            features = get_list_of_features_from_geojson_file(data_snapshot)
            print("Looping through the feature list and adding features to the DB.")
            for feature in features:
                ParcelHistorical.objects.create(data_geojson=feature,
                                                snapshot=new_snapshot)

        print(f"Start: {start_time}")
        print(f"End: {datetime.now()}")
