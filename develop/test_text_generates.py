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
            self.assertEqual(add_debug_text(item), "")

    def test_create_zoning_case_text(self):
        from develop.management.commands.scrape import create_zoning_case_text
        from develop.models import Zoning

        # --- Scenario 1: Normal valid case ---
        z1 = Zoning(zpyear=2025, zpnum=44)
        self.assertEqual(create_zoning_case_text(z1), "## Z-44-25\n")

        # --- Scenario 2: Another normal case ---
        z2 = Zoning(zpyear=2031, zpnum=7)
        self.assertEqual(create_zoning_case_text(z2), "## Z-7-31\n")

        # --- Scenario 3: Year with fewer than 4 digits (edge case) ---
        z3 = Zoning(zpyear=89, zpnum=10)  # expecting last 2 digits
        self.assertEqual(create_zoning_case_text(z3), "## Z-10-89\n")

        # --- Scenario 4: zpyear is None ---
        z4 = Zoning(zpyear=None, zpnum=55)
        self.assertEqual(create_zoning_case_text(z4), "## Z-55-\n")

        # --- Scenario 5: zpnum is None ---
        z5 = Zoning(zpyear=2024, zpnum=None)
        self.assertEqual(create_zoning_case_text(z5), "## Z--24\n")

        # --- Scenario 6: Both zpyear and zpnum None ---
        z6 = Zoning(zpyear=None, zpnum=None)
        self.assertEqual(create_zoning_case_text(z6), "## Z--\n")


