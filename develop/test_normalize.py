from django.test import SimpleTestCase

from develop.normalize import is_cosmetic_change
from develop.normalize import normalize_for_comparison
from develop.normalize import values_are_equivalent


class NormalizeTestCase(SimpleTestCase):
    def test_the_z_50_25_case(self):
        """The re-typed hearing date that prompted all of this.

        Z-50-25 produced a Discourse post whose only reported change was the
        zero-padding on the day.
        """
        self.assertTrue(values_are_equivalent(
            "City Council Public Hearing 10/6/26",
            "City Council Public Hearing 10/06/26"
        ))

    def test_date_separators_and_year_lengths(self):
        self.assertTrue(values_are_equivalent("Approved 10/6/26", "Approved 10/06/2026"))
        self.assertTrue(values_are_equivalent("Approved 10-6-26", "Approved 10/06/26"))
        self.assertTrue(values_are_equivalent("Approved 10.6.26", "Approved 10/06/26"))

    def test_real_date_change_is_not_cosmetic(self):
        self.assertFalse(values_are_equivalent(
            "City Council Public Hearing 10/6/26",
            "City Council Public Hearing 10/20/26"
        ))
        self.assertFalse(values_are_equivalent("Approved 10/6/26", "Approved 11/6/26"))
        self.assertFalse(values_are_equivalent("Approved 10/6/26", "Approved 10/6/27"))

    def test_real_status_change_is_not_cosmetic(self):
        self.assertFalse(values_are_equivalent(
            "City Council Public Hearing 10/6/26",
            "Planning Commission 10/6/26"
        ))

    def test_whitespace(self):
        self.assertTrue(values_are_equivalent(
            "City Council Public Hearing 10/6/26",
            "  City Council  Public Hearing\t10/6/26 "
        ))
        # &nbsp; is all over the city's tables.
        self.assertTrue(values_are_equivalent("Approved 11/04/25", "Approved\xa011/04/25\xa0"))
        self.assertTrue(values_are_equivalent("Approved 11/04/25", "Approved\n11/04/25"))

    def test_case_is_folded(self):
        self.assertTrue(values_are_equivalent(
            "City Council Public Hearing 10/6/26",
            "CITY COUNCIL PUBLIC HEARING 10/6/26"
        ))

    def test_none_and_empty_string_are_equivalent(self):
        self.assertTrue(values_are_equivalent(None, ""))
        self.assertTrue(values_are_equivalent(None, "   "))
        self.assertTrue(values_are_equivalent("", None))
        self.assertFalse(values_are_equivalent(None, "Approved"))

    def test_four_digit_years_are_left_alone(self):
        """The date rule must not reach into ISO-ish dates or URL paths."""
        self.assertEqual(normalize_for_comparison("2025/10/06"), "2025/10/06")
        self.assertFalse(values_are_equivalent("2025/10/06", "2025/10/6"))

    def test_plan_urls_are_left_alone(self):
        url = ("https://cityofraleigh0drupal.blob.core.usgovcloudapi.net/"
               "drupal-prod/COR22/Z-050-25.pdf")
        self.assertEqual(normalize_for_comparison(url), url.casefold())
        self.assertFalse(values_are_equivalent(url, url.replace("Z-050-25", "Z-051-25")))

    def test_non_string_values(self):
        self.assertTrue(values_are_equivalent(2025, "2025"))
        self.assertFalse(values_are_equivalent(2025, 2026))

    def test_is_cosmetic_change(self):
        self.assertTrue(is_cosmetic_change(
            "City Council Public Hearing 10/6/26",
            "City Council Public Hearing 10/06/26"
        ))
        # Identical values did not change at all, cosmetically or otherwise.
        self.assertFalse(is_cosmetic_change("Approved 10/06/26", "Approved 10/06/26"))
        self.assertFalse(is_cosmetic_change(None, None))
        # A real change is not a cosmetic one.
        self.assertFalse(is_cosmetic_change("Approved 10/06/26", "Approved 10/20/26"))
