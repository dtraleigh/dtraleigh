from django.test import SimpleTestCase
from django.test import TestCase
from develop.management.commands.text_generates import *
from develop.test_data import *

from django.conf import settings

from develop.test_data.create_test_data import *


class TextGenTestCaseDjango(TestCase):
    @classmethod
    def setUpTestData(cls):
        # create_test_data_dev_plans() Won't test this as we don't use this data ATM
        create_test_data_aads()
        create_test_data_zoning()
        create_test_data_site_reviews()
        create_test_data_tccs()

    def test_add_debug_text(self):
        all_test_items = SiteReviewCase.objects.all()
        for item in all_test_items:
            if settings.DEVELOP_INSTANCE == "Develop":
                self.assertNotEqual(add_debug_text(item), "")
            else:
                self.assertEqual(add_debug_text(item), "")
