from django.test import TestCase

from parcels.history import get_parcel_history_diffs, get_parcel_history_table_headers
from parcels.models import Parcel, RaleighSubsection, ParcelHistorical, Snapshot


class ParcelTestCase(TestCase):
    databases = "__all__"
    fixtures = ["parcels_test_data", "raleigh_subsections"]

    def setUp(self):
        Snapshot.objects.create(name="Test Snapshot")

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

    def test_parcel_is_fully_in_or_out_of_a_subsection(self):
        test_subsection1 = RaleighSubsection.objects.get(id=186)
        test_subsection2 = RaleighSubsection.objects.get(id=190)

        data_geojson = {'type':'Feature','geometry':{'type':'Polygon','coordinates':[[[-78.62529430472327,
                     35.77710487969577],[-78.62529430472327,35.77689897602288],[-78.62492947413203,35.77689897602288],
                      [-78.62492947413203,35.77710487969577],[-78.62529430472327,35.77710487969577]]]},'properties':{}}
        freeman_parcel = ParcelHistorical.objects.create(data_geojson=data_geojson,
                                                         snapshot=Snapshot.objects.get(name="Test Snapshot"))

        self.assertTrue(freeman_parcel.get_geosgeom_object().intersects(test_subsection1.geom))
        self.assertFalse(freeman_parcel.get_geosgeom_object().intersects(test_subsection2.geom))

        # Get the query right
        overlapping_subsections = RaleighSubsection.objects.filter(
                                                        geom__intersects=freeman_parcel.get_geosgeom_object())

        self.assertEqual([s.id for s in overlapping_subsections], [186])

    def test_parcel_overlaps_multiple_subsections(self):
        test_subsection1 = RaleighSubsection.objects.get(id=186)
        test_subsection2 = RaleighSubsection.objects.get(id=190)

        data_geojson = {'type':'Feature','geometry':{'type':'Polygon','coordinates':[[[-78.62983035930512,
                   35.77805532317532],[-78.62914098450993,35.77805532317532],[-78.62914098450993,35.77889549477342],
                  [-78.62983035930512,35.77889549477342],[-78.62983035930512,35.77805532317532]]]},'properties':{}}
        wym_academy_parcel = ParcelHistorical.objects.create(data_geojson=data_geojson,
                                                             snapshot=Snapshot.objects.get(name="Test Snapshot"))

        self.assertTrue(wym_academy_parcel.get_geosgeom_object().intersects(test_subsection1.geom))
        self.assertTrue(wym_academy_parcel.get_geosgeom_object().intersects(test_subsection2.geom))

        # Get the query right
        overlapping_subsections = RaleighSubsection.objects.filter(
                                                        geom__intersects=wym_academy_parcel.get_geosgeom_object())

        self.assertEqual([s.id for s in overlapping_subsections], [186, 190])
