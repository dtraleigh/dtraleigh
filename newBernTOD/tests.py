from django.test import TestCase

from newBernTOD.models import NewBernParcel
from parcels.functions_scan import difference_exists, update_parcel_is_active


class TODTestCase(TestCase):
    databases = "__all__"

    def test_difference_exists(self):
        self.assertFalse(difference_exists("Address 1", "Address 1"))
        self.assertFalse(difference_exists(1, 1))
        self.assertFalse(difference_exists(1.0, 1.0))
        self.assertTrue(difference_exists("Address 1", "Address 2"))
        self.assertTrue(difference_exists(1, 2))
        self.assertTrue(difference_exists(1.0, 1.1))

        test_parcel = NewBernParcel.objects.create(
            objectid=0,
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

    def test_update_parcel_is_active(self):
        test_parcel1 = NewBernParcel.objects.create(
            objectid=0,
            property_address="123 Test Street",
            bldg_val=100,
            totsalprice=150.15,
            is_active=True
        )
        active_parcels = NewBernParcel.objects.filter(is_active=True)
        active_parcels_objectids = [p.objectid for p in active_parcels]

        test_parcel2 = NewBernParcel.objects.create(
            objectid=1,
            property_address="456 Test Street",
            bldg_val=100,
            totsalprice=150.15,
            is_active=True
        )

        update_parcel_is_active(active_parcels_objectids, NewBernParcel.objects.filter(is_active=True), False)
        test_parcel2.refresh_from_db()
        self.assertFalse(test_parcel2.is_active, f"test_parcel2.is_active = {test_parcel2.is_active}")
