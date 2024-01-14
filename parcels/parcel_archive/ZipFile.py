import zipfile
import os


class ZipFile:
    def __init__(self, filename):
        self.filename = filename
        self.parent_zip_root_dir = "parcel_zips"
        self.parent_data_dir = "parcel_data"

    def __repr__(self):
        return f"Data from '{self.filename}'"

    @property
    def has_been_unzipped(self):
        return os.path.isdir(f"{self.parent_data_dir}\\{self.filename.split('.')[0]}")

    def unzip_the_file(self):
        if not self.has_been_unzipped:
            print(f"Unzipping {self.filename}.")
            with zipfile.ZipFile(f"{self.parent_zip_root_dir}\\{self.filename}", 'r') as zip_ref:
                zip_ref.extractall(f"{self.parent_data_dir}\\{self.filename.split('.')[0]}")
                return True
        else:
            print(f"Directory {self.filename.split('.')[0]} already exists.")
            return False
