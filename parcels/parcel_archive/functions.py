import json
import os
import sys

import geopandas
from django.contrib.gis.geos import GEOSGeometry
from pyproj import Transformer, transform

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
    path_to_shp_file = f"{data_snapshot.directory_path_and_name}\\{data_snapshot.get_shp_data_file}"
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
    path_to_shp_file = f"{data_snapshot.directory_path_and_name}\\{data_snapshot.get_shp_data_file}"
    if path_to_shp_file:
        print(f"reading {path_to_shp_file} for column names.")
        gdf = geopandas.read_file(path_to_shp_file)
        return gdf.to_json()
    raise Exception("path_to_shp_file is none.")


def create_geojson_file_from_shp(data_snapshot):
    path_to_shp_file = f"{data_snapshot.directory_path_and_name}\\{data_snapshot.get_shp_data_file}"
    if path_to_shp_file:
        print(f"Creating geojson file from {path_to_shp_file}.")
        gdf = geopandas.read_file(path_to_shp_file)
        geojson_file_name = f"{base_path}geojson_files\\{data_snapshot.get_shp_data_file[:-4]}.geojson"
        gdf.to_file(geojson_file_name, driver="GeoJSON")
        return geojson_file_name
    raise Exception("path_to_shp_file is none.")


def get_list_of_features_from_geojson_file(data_snapshot):
    with open(data_snapshot.geojson_data_file_w_path, "r") as read_file:
        data = json.load(read_file)

        return data["features"]


def parcel_has_CITY_value(parcel):
    try:
        if "CITY" in parcel.data_geojson["properties"]:
            return True
        return False
    except KeyError as e:
        print(e)


def get_list_of_all_possible_CITY_values(parcels):
    list_of_CITY_values = []
    for parcel in parcels:
        if parcel.data_geojson["properties"]["CITY"] not in list_of_CITY_values:
            list_of_CITY_values.append(parcel.data_geojson["properties"]["CITY"])

    return list_of_CITY_values


def switch_coordinates(coordinates):
    switched_coordinates = []
    if determine_geometry_type(coordinates) == "Polygon":
        for polygon in coordinates:
            switched_polygon = []
            for point in polygon:
                switched_point = [point[1], point[0]]
                switched_polygon.append(switched_point)
            switched_coordinates.append(switched_polygon)
    elif determine_geometry_type(coordinates) == "MultiPolygon":
        for polygon_set in coordinates:
            switched_polygon_set = []
            for polygon in polygon_set:
                switched_polygon = []
                for point in polygon:
                    switched_point = [point[1], point[0]]
                    switched_polygon.append(switched_point)
                switched_polygon_set.append(switched_polygon)
            switched_coordinates.append(switched_polygon_set)
    return switched_coordinates


def determine_geometry_type(coordinates):
    if len(coordinates) == 0:
        return None
    elif len(coordinates) == 1:
        return 'Polygon' if isinstance(coordinates[0][0], (tuple, list)) else None
    else:
        return 'MultiPolygon'


def add_polygon_type(parcel):
    geom_type_calculated = determine_geometry_type(parcel.data_geojson["geometry"])
    return {
        'type': geom_type_calculated,
        'coordinates': parcel.data_geojson["geometry"]
    }


def identify_coordinate_system(parcel):
    # Not scientific, just based on observations
    first_coord = get_first_coord(parcel)

    if (2000000 < first_coord[0] < 2200000) and (700000 < first_coord[1] < 810000):
        return "epsg:2264"
    elif (-79 < first_coord[0] < -77) and (34 < first_coord[1] < 36):
        return "epsg:4326"
    elif (-79 < first_coord[1] < -77) and (34 < first_coord[0] < 36):
        return "epsg:4326"
    else:
        return None


def get_first_coord(parcel):
    if "type" not in parcel.data_geojson["geometry"]:
        parcel.data_geojson["geometry"] = add_polygon_type(parcel)
    geom = GEOSGeometry(str(parcel.data_geojson["geometry"]))

    if geom.geom_type == "Polygon":
        first_coord = parcel.data_geojson["geometry"]["coordinates"][0][0]

    elif geom.geom_type == "MultiPolygon":
        first_coord = parcel.data_geojson["geometry"]["coordinates"][0][0][0]

    return first_coord


def verify_epsg4326_format(parcel):
    # want to see coordinates [-78.685, 35.751] rather than [35.751, -78.685]
    first_coord = get_first_coord(parcel)

    if (-79 < first_coord[1] < -77) and (34 < first_coord[0] < 36):
        updated_coords = switch_coordinates(parcel.data_geojson["geometry"]["coordinates"])
        type_of_geom = determine_geometry_type(updated_coords)
        return {'type': type_of_geom, 'coordinates': updated_coords}
    return parcel.data_geojson["geometry"]


def convert_geometry_to_epsg4326(geometry):
    converted_coordinates = []

    if "type" not in geometry:
        geometry["type"] = determine_geometry_type(geometry["coordinates"])

    geom = GEOSGeometry(str(geometry))

    if geom.geom_type == "Polygon":
        shape_coords = []
        for coord in geom.coords[0]:
            x, y = convert_epsg2264_to_epsg4326(coord[0], coord[1])
            shape_coords.append([y, x])
        converted_coordinates.append(shape_coords)

    elif geom.geom_type == "MultiPolygon":
        for shape in geom.coords:
            shape_coords = []
            for coord in shape[0]:
                x, y = convert_epsg2264_to_epsg4326(coord[0], coord[1])
                shape_coords.append([y, x])
            converted_coordinates.append([shape_coords])

    else:
        raise Exception("Unknown or unaccounted geom_type in parcel_archive.functions.convert_coordinates_to_epsg4326.")

    return {
        'type': geometry["type"],
        'coordinates': converted_coordinates
    }


def convert_epsg2264_to_epsg4326(x, y):
    transformer = Transformer.from_crs("epsg:2264", "epsg:4326")
    return transformer.transform(x, y)
