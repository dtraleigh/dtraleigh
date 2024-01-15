from DataSnapshot import DataSnapshot
from functions import get_zip_files_list, get_parcel_data_dirs, get_list_of_shp_col_names, reorder_lists, get_geojson_from_shp
from ZipFile import ZipFile
from prettytable import PrettyTable
import csv
from datetime import datetime

start_time = datetime.now()

results_table = PrettyTable()
results_table.field_names = ["Snapshot", "shp file"]


def create_col_names_csv(snapshots):
    with open("column_names_output.csv", "w", newline="") as file:
        writer = csv.writer(file)
        print(f"Creating column_names_output.csv file with {snapshots}")

        for snapshot in snapshots:
            snapshot.shp_col_name_list = get_list_of_shp_col_names(snapshot, True)
            snapshot.geojson = get_geojson_from_shp(snapshot)

        reorder_lists(snapshots)

        for snapshot in snapshots:
            writer.writerow([snapshot.directory_path_and_name] + snapshot.shp_col_name_list_aligned_w_others)


def get_geojson_data(snapshots):
    for snapshot in snapshots:
        snapshot.geojson = get_geojson_from_shp(snapshot)


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

# Logic to test
# create_col_names_csv(data_snapshots)
# get_geojson_data(data_snapshots) # Beware, the geojson file is big

# Read geojson into a file with
# gdf.to_file("test.geojson", driver="GeoJSON")

print(f"Start: {start_time}")
print(f"End: {datetime.now()}")
