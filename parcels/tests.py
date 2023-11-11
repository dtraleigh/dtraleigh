from django.test import TestCase

from parcels.history import get_parcel_history_diffs, get_parcel_history_table_headers
from parcels.models import Parcel


class ParcelTestCase(TestCase):
    databases = "__all__"
    fixtures = ["parcels_test_data"]

    def test_get_parcel_history_table_headers1(self):
        prop1 = Parcel.objects.get(addr1="208 FREEMAN ST")
        parcel_history_diffs_list1 = get_parcel_history_diffs(prop1.history.all())

        self.assertEqual(get_parcel_history_table_headers(parcel_history_diffs_list1), ["bldg_val"])

        prop2 = Parcel.objects.get(objectid=350951)
        parcel_history_diffs_list2 = get_parcel_history_diffs(prop2.history.all())

        self.assertEqual(get_parcel_history_table_headers(parcel_history_diffs_list2), [])

        prop3 = Parcel.objects.get(objectid=205)
        parcel_history_diffs_list3 = get_parcel_history_diffs(prop3.history.all())

        self.assertEqual(get_parcel_history_table_headers(parcel_history_diffs_list3), ["owner"])

        prop4 = Parcel.objects.get(objectid=131225)
        parcel_history_diffs_list4 = get_parcel_history_diffs(prop4.history.all())

        self.assertEqual(get_parcel_history_table_headers(parcel_history_diffs_list4), [])
