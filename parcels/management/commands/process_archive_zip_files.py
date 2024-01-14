from django.core.management.base import BaseCommand

from datetime import datetime
from prettytable import PrettyTable
from parcels.parcel_archive.ZipFile import ZipFile
from parcels.parcel_archive.DataSnapshot import DataSnapshot

from parcels.parcel_archive.functions import get_zip_files_list, get_parcel_data_dirs


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
            results_table.add_row([data_snapshot.directory_name, data_snapshot.get_shp_data_file])

        print(results_table)

        print(f"Start: {start_time}")
        print(f"End: {datetime.now()}")
