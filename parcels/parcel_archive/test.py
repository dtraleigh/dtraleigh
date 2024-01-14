import shutil
import unittest
import os

from DataSnapshot import DataSnapshot
from ZipFile import ZipFile
from functions import reorder_lists


class TestZipFile(unittest.TestCase):

    test_zip_file_name = "empty_doc_for_testing.zip"

    @classmethod
    def setUpClass(cls):
        shutil.copyfile(f"test_data\\{cls.test_zip_file_name}", f"parcel_zips\\{cls.test_zip_file_name}")

    def tearDown(self):
        shutil.rmtree(f"parcel_data\\{self.test_zip_file_name.split('.')[0]}")

    @classmethod
    def tearDownClass(cls):
        os.remove(f"parcel_zips\\{cls.test_zip_file_name}")

    def test_unzip_the_file1(self):
        """
        Unzip the test zip file
        """
        test_zip_file = ZipFile(f"{self.test_zip_file_name}")
        test_zip_file.unzip_the_file()
        self.assertTrue(os.path.isdir(f"parcel_data\\{self.test_zip_file_name.split('.')[0]}"))

    def test_unzip_the_file2(self):
        """
        Try to unzip a file that's already been unzipped
        """
        test_zip_file = ZipFile(f"{self.test_zip_file_name}")
        self.assertTrue(test_zip_file.unzip_the_file())
        self.assertTrue(os.path.isdir(f"parcel_data\\{self.test_zip_file_name.split('.')[0]}"))
        self.assertFalse(test_zip_file.unzip_the_file())
        self.assertTrue(os.path.isdir(f"parcel_data\\{self.test_zip_file_name.split('.')[0]}"))


class TestDataSnapshot(unittest.TestCase):

    test_dir_name = "test_dir"

    def setUp(self):
        shutil.copytree(f"test_data\\{self.test_dir_name}", f"parcel_data\\{self.test_dir_name}")

    def tearDown(self):
        shutil.rmtree(f"parcel_data\\{self.test_dir_name}")

    def test_contains_shp_data(self):
        snapshot = DataSnapshot(f"parcel_data\\{self.test_dir_name}")
        self.assertFalse(snapshot.contains_shp_data)

        first_shp_file = open(f"parcel_data\\{self.test_dir_name}\\file1.shp", "x")
        first_shp_file.close()
        self.assertTrue(snapshot.contains_shp_data)

        second_shp_file = open(f"parcel_data\\{self.test_dir_name}\\file2.shp", "x")
        second_shp_file.close()
        with self.assertRaises(Exception):
            snapshot.contains_shp_data

    def test_get_shp_data_file(self):
        snapshot = DataSnapshot(f"parcel_data\\{self.test_dir_name}")
        self.assertEqual(snapshot.get_shp_data_file, None)

        first_shp_file = open(f"parcel_data\\{self.test_dir_name}\\file1.shp", "x")
        first_shp_file.close()
        self.assertEqual(snapshot.get_shp_data_file, "file1.shp")


class TestFunctions(unittest.TestCase):

    def test_reorder_lists(self):
        data_snapshots = [
            DataSnapshot("test_snap1", True),
            DataSnapshot("test_snap2", True),
            DataSnapshot("test_snap3", True),
        ]

        data_snapshots[0].shp_col_name_list = ["Apple", "Bananas", "Cherries", "Durian"]
        data_snapshots[1].shp_col_name_list = ["Apple", "Bananas", "Durian", "Endive"]
        data_snapshots[2].shp_col_name_list = ["Bananas", "Durian", "Endive", "Yam"]

        reorder_lists(data_snapshots)

        actual = [
            data_snapshots[0].shp_col_name_list_aligned_w_others,
            data_snapshots[1].shp_col_name_list_aligned_w_others,
            data_snapshots[2].shp_col_name_list_aligned_w_others
        ]

        expected = [
            ["Apple", "Bananas", "Cherries", "Durian", "", ""],
            ["Apple", "Bananas", "", "Durian", "Endive", ""],
            ["", "Bananas", "", "Durian", "Endive", "Yam"]
        ]

        self.assertEqual(actual, expected)

    def test_create_geojson_file_from_shp(self):
        expected_file = "geojson_files\\Raleigh_City_Council_Districts.geojson"

        data1 = DataSnapshot("test_data")
        data1.extract_geojson_from_shp()
        self.assertTrue(os.path.isfile(expected_file))
        os.remove(expected_file)


if __name__ == "__main__":
    unittest.main()
