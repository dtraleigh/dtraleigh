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


class DifferenceTableTestCase(TestCase):
    """What the UPDATES table reports, and when it reports nothing at all."""

    def setUp(self):
        self.zon = Zoning.objects.create(
            zpyear=2025,
            zpnum=50,
            location="2233 & 2321 Capital Blvd",
            status="City Council Public Hearing 10/6/26",
            plan_url="https://example.com/Z-050-25.pdf"
        )

    def test_no_previous_record_reports_nothing(self):
        """One history row means there is nothing to diff against.

        Reporting every field as "None -> value" was the old behaviour, via a
        swallowed AttributeError in get_field_value.
        """
        self.assertEqual(self.zon.history.count(), 1)
        self.assertEqual(get_difference_rows(self.zon), [])
        self.assertEqual(difference_table_output(self.zon), "")

    def test_real_status_change_reports_one_row(self):
        self.zon.status = "City Council Public Hearing 10/20/26"
        self.zon.save()

        rows = get_difference_rows(self.zon)

        self.assertEqual(len(rows), 1)
        label, old_value, new_value = rows[0]
        self.assertEqual(label, "Status")
        self.assertEqual(old_value, "City Council Public Hearing 10/6/26")
        self.assertEqual(new_value, "City Council Public Hearing 10/20/26")

        table = difference_table_output(self.zon)
        self.assertIn("### UPDATES", table)
        self.assertIn("|Status|City Council Public Hearing 10/6/26|"
                      "City Council Public Hearing 10/20/26|", table)

    def test_cosmetic_change_in_history_reports_nothing(self):
        """The scrape should catch these first, but a manual admin edit would not."""
        self.zon.status = "City Council Public Hearing 10/06/26"
        self.zon.save()

        self.assertEqual(self.zon.history.count(), 2)
        self.assertEqual(get_difference_rows(self.zon), [])
        self.assertEqual(difference_table_output(self.zon), "")

    def test_multiple_changed_fields_each_get_a_row(self):
        self.zon.status = "Approved 10/20/26"
        self.zon.location = "2233 Capital Blvd"
        self.zon.save()

        labels = [row[0] for row in get_difference_rows(self.zon)]

        self.assertCountEqual(labels, ["Status", "Location"])

    def test_pipes_and_newlines_stay_inside_one_row(self):
        """A raw pipe opens a column and a raw newline ends the row."""
        self.zon.status = "Approved 10/20/26 | see notes\nSecond line"
        self.zon.save()

        table = difference_table_output(self.zon)
        data_rows = [line for line in table.splitlines() if line.startswith("|Status|")]

        self.assertEqual(len(data_rows), 1)
        self.assertIn("\\|", data_rows[0])
        self.assertIn("see notes Second line", data_rows[0])
        # Once the escaped pipes are discounted, the row still has exactly the
        # four column separators of |label|previous|new|.
        self.assertEqual(data_rows[0].replace("\\|", "").count("|"), 4)

    def test_escape_table_cell(self):
        self.assertEqual(escape_table_cell("a|b"), "a\\|b")
        self.assertEqual(escape_table_cell("a\nb"), "a b")
        self.assertEqual(escape_table_cell("a\r\nb"), "a b")
        self.assertEqual(escape_table_cell(None), "None")
