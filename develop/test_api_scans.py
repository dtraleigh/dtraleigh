from django.test import SimpleTestCase
from develop.management.commands.api_scans import *
from datetime import datetime


class APIScansTestCase(SimpleTestCase):
    def test_clean_unix_date(self):
        year1 = 1374724800000
        self.assertEqual(clean_unix_date(year1),
                         datetime.utcfromtimestamp(year1 / 1000))

        year2 = 150895422
        self.assertEqual(clean_unix_date(year2), None)

        year3 = "1603598400000"
        self.assertEqual(clean_unix_date(year3), None)

        year4 = None
        self.assertEqual(clean_unix_date(year4), None)
