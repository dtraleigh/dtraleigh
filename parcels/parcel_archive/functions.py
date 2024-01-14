import os
import geopandas

base_path = "parcels\\parcel_archive\\"


def get_zip_files_list():
    list_of_zip_files = []

    for file in os.listdir(f"{base_path}parcel_zips"):
        if file.endswith(".zip"):
            list_of_zip_files.append(file)

    return list_of_zip_files


def get_parcel_data_dirs():
    return [f.path for f in os.scandir(f"{base_path}parcel_data") if f.is_dir()]


def get_list_of_shp_col_names(data_snapshot, alpha_sorted=False):
    path_to_shp_file = f"{data_snapshot.directory_name}\\{data_snapshot.get_shp_data_file}"
    if path_to_shp_file:
        print(f"reading {path_to_shp_file} for column names.")
        gdf = geopandas.read_file(path_to_shp_file)
        list_of_col_names = list(gdf)
        if alpha_sorted:
            return sorted(list_of_col_names, key=str.lower)
        return list_of_col_names
    raise Exception("path_to_shp_file is none.")


def reorder_lists(data_snapshots):
    lists = []
    for data_snapshot in data_snapshots:
        lists.append(data_snapshot.shp_col_name_list)

    flat_list = [item for sublist in lists for item in sublist]
    unique_strings = list(set(flat_list))
    sorted_unique_strings = sorted(unique_strings, key=str.lower)
    reordered_lists = [[s if s in sublist else '' for s in sorted_unique_strings] for sublist in lists]

    for lst, dts in zip(reordered_lists, data_snapshots):
        dts.shp_col_name_list_aligned_w_others = lst


def get_geojson_from_shp(data_snapshot):
    path_to_shp_file = f"{data_snapshot.directory_name}\\{data_snapshot.get_shp_data_file}"
    if path_to_shp_file:
        print(f"reading {path_to_shp_file} for column names.")
        gdf = geopandas.read_file(path_to_shp_file)
        return gdf.to_json()
    raise Exception("path_to_shp_file is none.")


def create_geojson_file_from_shp(data_snapshot):
    path_to_shp_file = f"{data_snapshot.directory_name}\\{data_snapshot.get_shp_data_file}"
    if path_to_shp_file:
        print(f"Creating geojson file from {path_to_shp_file}.")
        gdf = geopandas.read_file(path_to_shp_file)
        geojson_file_name = f"{base_path}geojson_files\\{data_snapshot.get_shp_data_file[:-4]}.geojson"
        gdf.to_file(geojson_file_name, driver="GeoJSON")
        return geojson_file_name
    raise Exception("path_to_shp_file is none.")
