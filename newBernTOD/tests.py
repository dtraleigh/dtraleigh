from django.test import SimpleTestCase
from django.test import TestCase

from newBernTOD.management.commands.update_existing_parcels import difference_exists
from newBernTOD.models import Parcel


class TODTestCase(TestCase):
    def test_difference_exists(self):
        self.assertFalse(difference_exists("Address 1", "Address 1"))
        self.assertFalse(difference_exists(1, 1))
        self.assertFalse(difference_exists(1.0, 1.0))
        self.assertTrue(difference_exists("Address 1", "Address 2"))
        self.assertTrue(difference_exists(1, 2))
        self.assertTrue(difference_exists(1.0, 1.1))

        test_parcel = Parcel.objects.create(
            property_address="123 Test Street",
            bldg_val=100,
            totsalprice=150.15
        )

        self.assertFalse(difference_exists(test_parcel.property_address, "123 Test Street"))
        self.assertFalse(difference_exists(test_parcel.bldg_val, 100))
        self.assertFalse(difference_exists(test_parcel.totsalprice, 150.15))
        self.assertTrue(difference_exists(test_parcel.property_address, "1234 Test Street"))
        self.assertTrue(difference_exists(test_parcel.bldg_val, 115))
        self.assertTrue(difference_exists(test_parcel.totsalprice, 165.44))

        test_parcel.delete()
