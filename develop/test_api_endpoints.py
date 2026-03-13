import requests
from bs4 import BeautifulSoup
from django.test import SimpleTestCase

from develop.management.commands.actions import get_api_json, get_total_developments
from develop.management.commands.location import get_lat_lon_by_pin, get_parcel_by_pin
from develop.management.commands.scrape import get_page_content
from develop.views import get_ncod_data

ARCGIS_DEV_PLANS_URL = (
    "https://services.arcgis.com/v400IkDOw1ad7Yad/arcgis/rest/services"
    "/Development_Plans/FeatureServer/0/query"
)


class ArcGISDevelopmentPlansAPITest(SimpleTestCase):
    """Validates the ArcGIS Development Plans FeatureServer API."""

    def test_total_count_is_positive_integer(self):
        count = get_total_developments()
        self.assertIsInstance(count, int)
        self.assertGreater(count, 0)

    def test_feature_query_returns_features(self):
        url = f"{ARCGIS_DEV_PLANS_URL}?where=submitted_yr>=2022&outFields=*&outSR=4326&f=json"
        data = get_api_json(url)
        self.assertIsInstance(data, dict)
        self.assertIn("features", data)
        self.assertIsInstance(data["features"], list)
        self.assertGreater(len(data["features"]), 0)

    def test_feature_attributes_have_expected_fields(self):
        url = f"{ARCGIS_DEV_PLANS_URL}?where=submitted_yr>=2022&outFields=*&outSR=4326&f=json"
        data = get_api_json(url)
        attributes = data["features"][0]["attributes"]
        self.assertIn("plan_number", attributes)
        self.assertIn("submitted_yr", attributes)


class RaleighMapsNCODAPITest(SimpleTestCase):
    """Validates the Raleigh Maps NCOD overlay API."""

    def setUp(self):
        self.response = get_ncod_data()
        self.data = self.response.json()

    def test_ncod_returns_200(self):
        self.assertEqual(self.response.status_code, 200)

    def test_ncod_response_has_features(self):
        self.assertIn("features", self.data)
        self.assertIsInstance(self.data["features"], list)
        self.assertGreater(len(self.data["features"]), 0)

    def test_ncod_feature_has_geometry(self):
        self.assertIsNotNone(self.data["features"][0]["geometry"])


class RaleighMapsDXZoningAPITest(SimpleTestCase):
    """Validates the Raleigh Maps DX Zoning API endpoints used in views."""

    DX_URL = (
        "https://maps.raleighnc.gov/arcgis/rest/services/Planning/Zoning/MapServer/0/query"
        "?outFields=*&outSR=4326&f=json&where=ZONE_TYPE='DX-'"
    )
    DX40_URL = (
        "https://maps.raleighnc.gov/arcgis/rest/services/Planning/Zoning/MapServer/0/query"
        "?outFields=*&outSR=4326&f=json&where=HEIGHT>30 AND ZONE_TYPE='DX-'"
    )

    def test_dx_zoning_returns_200(self):
        response = requests.request("GET", self.DX_URL, headers={}, data={})
        self.assertEqual(response.status_code, 200)

    def test_dx_zoning_has_features(self):
        response = requests.request("GET", self.DX_URL, headers={}, data={})
        data = response.json()
        self.assertIn("features", data)
        self.assertIsInstance(data["features"], list)
        self.assertGreater(len(data["features"]), 0)

    def test_dx_zoning40_returns_200(self):
        response = requests.request("GET", self.DX40_URL, headers={}, data={})
        self.assertEqual(response.status_code, 200)

    def test_dx_zoning40_has_features(self):
        response = requests.request("GET", self.DX40_URL, headers={}, data={})
        data = response.json()
        self.assertIn("features", data)
        self.assertIsInstance(data["features"], list)
        self.assertGreater(len(data["features"]), 0)


class WakeCountyPropertyAPITest(SimpleTestCase):
    """Validates the Wake County property/address API."""

    # A known valid PIN from the Wake County address database
    KNOWN_PIN = "0609625590"
    BASE_URL = "http://maps.wakegov.com/arcgis/rest/services/Property/Addresses/MapServer/0/query"

    def test_count_query_returns_positive_total(self):
        url = f"{self.BASE_URL}?where=1%3D1&returnCountOnly=true&f=json"
        response = requests.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("count", data)
        self.assertGreater(data["count"], 0)

    def test_get_lat_lon_returns_coordinates(self):
        lat, lon = get_lat_lon_by_pin(self.KNOWN_PIN)
        self.assertIsNotNone(lat)
        self.assertIsNotNone(lon)
        # Sanity-check coordinates are in Wake County
        self.assertGreater(lat, 35.5)
        self.assertLess(lat, 36.1)
        self.assertGreater(lon, -79.1)
        self.assertLess(lon, -78.2)

    def test_get_parcel_returns_attributes(self):
        attributes = get_parcel_by_pin(self.KNOWN_PIN)
        self.assertIsInstance(attributes, dict)
        self.assertIn("PIN_NUM", attributes)


class RaleighWebPagesAPITest(SimpleTestCase):
    """Validates the City of Raleigh web pages scraped by the develop app."""

    ZONING_URL = "https://raleighnc.gov/planning/services/rezoning-process/rezoning-cases"
    TEXT_CHANGES_URL = "https://raleighnc.gov/planning/services/text-changes/text-change-cases"
    NEIGHBORHOOD_URL = "https://raleighnc.gov/planning/services/rezoning-process/neighborhood-meetings"
    DEV_STATUS_URL = "https://www.raleighnc.gov/development"

    def test_zoning_cases_page_returns_soup(self):
        soup = get_page_content(self.ZONING_URL)
        self.assertIsInstance(soup, BeautifulSoup)
        self.assertIsNotNone(soup.find("table"))

    def test_text_changes_page_returns_soup(self):
        soup = get_page_content(self.TEXT_CHANGES_URL)
        self.assertIsInstance(soup, BeautifulSoup)
        self.assertIsNotNone(soup.find("table"))

    def test_neighborhood_meetings_page_returns_soup(self):
        soup = get_page_content(self.NEIGHBORHOOD_URL)
        self.assertIsInstance(soup, BeautifulSoup)
        self.assertIsNotNone(soup.find("table"))

    def test_development_status_page_returns_200(self):
        response = requests.get(self.DEV_STATUS_URL, timeout=10)
        self.assertEqual(response.status_code, 200)
