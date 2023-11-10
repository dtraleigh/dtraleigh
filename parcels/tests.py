from django.test import TestCase

from parcels.models import Parcel


class ParcelTestCase(TestCase):
    databases = "__all__"
    fixtures = ["parcels_test_data"]

    def test_something(self):
        house = Parcel.objects.get(addr1="208 FREEMAN ST")
        self.assertEqual(house.owner, "SUAREZ, LEO S. SUAREZ, JENNIFER S.")
