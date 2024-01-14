import os

from parcels.parcel_archive.functions import create_geojson_file_from_shp

base_path = "parcels\\parcel_archive\\"


class DataSnapshot:
    def __init__(self, directory_path_and_name, is_test=False):
        self.directory_name = directory_path_and_name
        self.file_list = self.get_file_list(is_test)
        self.shp_file_name = ""
        self.shp_col_name_list = []
        self.shp_col_name_list_aligned_w_others = []
        self.geojson_data_file_w_path = self.get_geojson_file_name_if_exists()

    def __repr__(self):
        return f"Snapshot files from {base_path}{self.directory_name}"

    def get_file_list(self, is_test=False):
        if is_test:
            return self.directory_name
        return [file for file in os.listdir(self.directory_name)]

    @property
    def contains_shp_data(self):
        file_list = self.get_file_list()

        shp_files = []
        for file in file_list:
            if file.split(".")[-1] == "shp":
                shp_files.append(file)

        if len(shp_files) == 0:
            return False
        elif len(shp_files) == 1:
            return True
        else:
            raise Exception(f"{base_path}{self.directory_name} contains multiple .shp files, {shp_files}")

    @property
    def get_shp_data_file(self):
        if self.contains_shp_data:
            self.shp_file_name = [file for file in self.get_file_list() if file.split(".")[-1] == "shp"][0]
            return self.shp_file_name
        return None

    def get_geojson_file_name_if_exists(self):
        geojson_folder_content = [file for file in os.listdir(f"{base_path}geojson_files")]
        for filename in geojson_folder_content:
            if self.shp_file_name in filename.split(".")[0]:
                return f"{base_path}{filename}"
        return ""

    def extract_geojson_from_shp(self):
        if self.geojson_data_file_w_path == "":
            self.geojson_data_file_w_path = create_geojson_file_from_shp(self)
            return f"geojson file created at {self.geojson_data_file_w_path}."
        return f"geojson file exists at {self.geojson_data_file_w_path}."
