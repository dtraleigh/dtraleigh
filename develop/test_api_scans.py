import io
import re
from unittest.mock import patch

from django.core import mail
from django.test import SimpleTestCase, TestCase
from develop.management.commands import actions
from develop.management.commands import api_scans
from develop.management.commands.api_scans import *
from develop.management.commands.actions import DEVELOPMENT_FIELDS_TO_COMPARE
from develop.management.commands.actions import api_object_is_different
from develop.models import DevelopmentPlan
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


# One real feature off the Development Plans API, copied from the payload the
# scan logged when it could not create it. Kept whole rather than trimmed to the
# fields under test, so a key the scan reads but we forgot shows up as a KeyError
# here rather than in production.
KNOWLES_STREET = {
    "OBJECTID": 53454,
    "submitted": 1650465146000,
    "submitted_yr": 2022,
    "approved": 1674664668000,
    "plan_type": "DSLC - Preliminary Subdivision",
    "status": "Approved",
    "appealperiodends": 1677256668000,
    "updated": 1723562201000,
    "sunset_date": 1769299200000,
    "acreage": 15.69,
    "major_street": "100 Knowles St",
    "developer": "McAdams",
    "plan_name": "DSLC - 100 Knowles Street",
    "lots_req": 2,
    "lots_apprv": 2,
    "sq_ft_req": None,
    "units_apprv": None,
    "units_req": None,
    "zoning": "CM, CX-5-CU",
    "plan_number": "SUB-0029-2022",
    "GlobalID": "c3bbcbdf-67dd-4259-bb77-e58707aa6cd3",
    "missing_middle": "No",
}


def api_response(*attributes):
    return {"features": [{"attributes": dict(a), "geometry": {"x": -78.6, "y": 35.8}}
                         for a in attributes]}


class DevelopmentPlanScanTestCase(TestCase):
    """The scan has to actually land a plan in the DB, and notice when it moves."""

    def setUp(self):
        # Both are module-level and deduplicate for the life of the process, so a
        # previous test's complaint would otherwise silence this one's.
        actions._uncomparable_fields.clear()
        api_scans._failed_creates.clear()

    def scan(self, *attributes):
        with patch("develop.management.commands.api_scans.get_api_json") as mock_json:
            mock_json.return_value = api_response(*attributes)
            development_api_scan()

    def test_a_new_plan_is_created(self):
        """Regression: a stale create() kwarg meant no plan was ever created."""
        self.scan(KNOWLES_STREET)

        plan = DevelopmentPlan.objects.get(objectid=53454)

        self.assertEqual(plan.major_street, "100 Knowles St")
        self.assertEqual(plan.plan_name, "DSLC - 100 Knowles Street")
        self.assertEqual(plan.status, "Approved")

    def test_submitted_year_is_stored_on_the_field_that_exists(self):
        """submitted_yr is the API's name for it; the model field is submitted_field."""
        self.scan(KNOWLES_STREET)

        self.assertEqual(DevelopmentPlan.objects.get(objectid=53454).submitted_field, 2022)

    def test_scanning_twice_does_not_duplicate_the_plan(self):
        self.scan(KNOWLES_STREET)
        self.scan(KNOWLES_STREET)

        self.assertEqual(DevelopmentPlan.objects.filter(objectid=53454).count(), 1)

    def test_a_changed_major_street_is_noticed_and_stored(self):
        """Regression: the mapping key was stale, so major_street never compared,
        and the update assigned an attribute the model does not have."""
        self.scan(KNOWLES_STREET)

        moved = dict(KNOWLES_STREET, major_street="200 Knowles St")
        self.scan(moved)

        plan = DevelopmentPlan.objects.get(objectid=53454)

        self.assertEqual(plan.major_street, "200 Knowles St")
        self.assertEqual(plan.history.count(), 2)

    def test_an_unchanged_plan_is_not_rewritten(self):
        self.scan(KNOWLES_STREET)
        self.scan(KNOWLES_STREET)

        self.assertEqual(DevelopmentPlan.objects.get(objectid=53454).history.count(), 1)


class APIObjectIsDifferentTestCase(TestCase):
    """The comparison itself, without the scan around it."""

    def setUp(self):
        actions._uncomparable_fields.clear()

        self.plan = DevelopmentPlan.objects.create(
            objectid=53454,
            status="Approved",
            major_street="100 Knowles St",
            plan_name="DSLC - 100 Knowles Street",
            zoning="CM, CX-5-CU",
        )

    def test_identical_values_are_not_a_difference(self):
        self.assertFalse(api_object_is_different(self.plan, KNOWLES_STREET))

    def test_every_compared_field_resolves_to_an_api_key(self):
        """A compared field missing from the mapping used to log three lines per
        plan per run - one of them the whole payload - which is what grew
        debug.txt by 16MB in a day."""
        with self.assertNoLogs("django", level="WARNING"):
            api_object_is_different(self.plan, KNOWLES_STREET)

        self.assertEqual(actions._uncomparable_fields, set())

    def test_a_changed_major_street_is_a_difference(self):
        moved = dict(KNOWLES_STREET, major_street="200 Knowles St")

        self.assertTrue(api_object_is_different(self.plan, moved))

    def test_a_changed_status_is_a_difference(self):
        self.assertTrue(api_object_is_different(self.plan, dict(KNOWLES_STREET, status="Expired")))

    def test_a_retyped_value_is_not_a_difference(self):
        """Same normalize rules the scrape uses - see develop/normalize.py."""
        retyped = dict(KNOWLES_STREET, status="approved ")

        self.assertFalse(api_object_is_different(self.plan, retyped))

    def test_a_missing_api_key_is_reported_once_and_names_the_cause(self):
        without_street = {k: v for k, v in KNOWLES_STREET.items() if k != "major_street"}

        with self.assertLogs("django", level="WARNING") as logs:
            api_object_is_different(self.plan, without_street)
            api_object_is_different(self.plan, without_street)

        self.assertEqual(len(logs.output), 1)
        self.assertIn("Cannot compare major_street", logs.output[0])
        self.assertIn("no 'major_street' key", logs.output[0])

    def test_the_other_fields_are_still_compared_when_one_cannot_be(self):
        """A field we cannot read must not hide a change in one we can."""
        broken = {k: v for k, v in KNOWLES_STREET.items() if k != "major_street"}
        broken["status"] = "Expired"

        self.assertTrue(api_object_is_different(self.plan, broken))


def attributes_the_scan_reads():
    """The attribute_data keys api_scans actually reads, ignoring commented-out code.

    Read off the source rather than listed by hand, because a second hand-kept
    list would be one more thing to drift - which is the failure this whole
    contract exists to catch.
    """
    with io.open(api_scans.__file__, encoding="utf-8") as source:
        lines = source.read().splitlines()

    pattern = re.compile(r"""attribute_data(?:\[|\.get\()["']([^"']+)["']""")
    keys = set()

    for line in lines:
        if line.strip().startswith("#"):
            continue

        keys |= set(pattern.findall(line))

    return keys


class ContractDefinitionTestCase(SimpleTestCase):
    """The contract has to describe what the code really does, or it guards nothing."""

    def test_the_contract_lists_every_attribute_the_scan_reads(self):
        unlisted = attributes_the_scan_reads() - set(DEVELOPMENT_PLAN_ATTRIBUTES)

        self.assertEqual(unlisted, set(),
                         f"development_api_scan reads {sorted(unlisted)}, which the "
                         f"pre-check would not require. Add them to "
                         f"DEVELOPMENT_PLAN_ATTRIBUTES.")

    def test_the_contract_lists_nothing_the_scan_does_not_read(self):
        unused = set(DEVELOPMENT_PLAN_ATTRIBUTES) - attributes_the_scan_reads()

        self.assertEqual(unused, set(),
                         f"DEVELOPMENT_PLAN_ATTRIBUTES requires {sorted(unused)}, which "
                         f"the scan never reads. A response missing one would be "
                         f"rejected for no reason.")

    def test_every_compared_field_maps_into_the_contract(self):
        """api_object_is_different reads through developmentplan_mapping, so a field
        it compares has to land on an attribute the pre-check requires."""
        for field in DEVELOPMENT_FIELDS_TO_COMPARE:
            self.assertIn(field, DevelopmentPlan.developmentplan_mapping,
                          f"{field} has no entry in developmentplan_mapping.")
            self.assertIn(DevelopmentPlan.developmentplan_mapping[field],
                          DEVELOPMENT_PLAN_ATTRIBUTES)


class ContractMismatchTestCase(SimpleTestCase):
    """What the pre-check accepts, and how it describes what it rejects."""

    def test_a_good_response_is_accepted(self):
        self.assertEqual(describe_contract_mismatch(api_response(KNOWLES_STREET)), "")

    def test_an_extra_attribute_is_not_a_mismatch(self):
        """A column we do not read breaks nothing we do read."""
        extended = dict(KNOWLES_STREET, brand_new_column="whatever")

        self.assertEqual(describe_contract_mismatch(api_response(extended)), "")
        self.assertEqual(unknown_attributes(api_response(extended)), ["brand_new_column"])

    def test_a_renamed_attribute_is_a_mismatch_that_names_it(self):
        renamed = {k: v for k, v in KNOWLES_STREET.items() if k != "major_street"}
        renamed["majorstreet"] = "100 Knowles St"

        mismatch = describe_contract_mismatch(api_response(renamed))

        self.assertIn("major_street", mismatch)
        self.assertIn("1 of 1 features", mismatch)

    def test_a_partial_rename_says_how_widespread_it_is(self):
        dropped = {k: v for k, v in KNOWLES_STREET.items() if k != "zoning"}

        mismatch = describe_contract_mismatch(api_response(KNOWLES_STREET, dropped))

        self.assertIn("zoning (absent from 1 of 2 features)", mismatch)

    def test_an_arcgis_error_payload_is_a_mismatch(self):
        payload = {"error": {"code": 400, "message": "Invalid field: submitted_yr"}}

        self.assertIn("error payload", describe_contract_mismatch(payload))
        self.assertIn("Invalid field", describe_contract_mismatch(payload))

    def test_a_missing_features_key_is_a_mismatch_that_shows_what_came_back(self):
        mismatch = describe_contract_mismatch({"objectIdFieldName": "OBJECTID"})

        self.assertIn("no 'features' key", mismatch)
        self.assertIn("objectIdFieldName", mismatch)

    def test_an_empty_feature_list_is_a_mismatch(self):
        """The query covers 2022 onward, so nothing at all means something moved."""
        self.assertIn("empty", describe_contract_mismatch({"features": []}))

    def test_a_reshaped_feature_is_a_mismatch(self):
        self.assertIn("not shaped like",
                      describe_contract_mismatch({"features": [{"attrs": KNOWLES_STREET}]}))

    def test_a_non_dict_response_is_a_mismatch(self):
        """get_api_json hands back the raw response object on a non-200."""
        self.assertIn("rather than a JSON object", describe_contract_mismatch("<html>503</html>"))

    def test_no_response_at_all_is_a_mismatch(self):
        self.assertIn("nothing at all", describe_contract_mismatch(None))


class ContractGuardTestCase(TestCase):
    """The guard has to actually stop the scan and reach the admins."""

    def setUp(self):
        Subscriber.objects.create(name="Leo", email="leo@dtraleigh.com", is_bot=False)
        actions._uncomparable_fields.clear()
        api_scans._failed_creates.clear()
        mail.outbox = []

    def scan(self, payload):
        with patch("develop.management.commands.api_scans.get_api_json") as mock_json:
            mock_json.return_value = payload
            development_api_scan()

    def test_a_mismatch_stops_processing_before_anything_is_written(self):
        renamed = {k: v for k, v in KNOWLES_STREET.items() if k != "status"}
        renamed["case_status"] = "Approved"

        self.scan(api_response(renamed))

        self.assertEqual(DevelopmentPlan.objects.count(), 0)

    def test_a_mismatch_emails_the_admins_with_the_difference_and_the_fix(self):
        renamed = {k: v for k, v in KNOWLES_STREET.items() if k != "status"}

        self.scan(api_response(renamed))

        self.assertEqual(len(mail.outbox), 1)

        notice = mail.outbox[0]
        self.assertEqual(notice.to, ["leo@dtraleigh.com"])
        self.assertIn("contract mismatch", notice.subject)

        # The difference itself, and each place our side of it is written down.
        self.assertIn("status", notice.body)
        self.assertIn("DEVELOPMENT_PLAN_ATTRIBUTES", notice.body)
        self.assertIn("developmentplan_mapping", notice.body)
        self.assertIn("development_api_scan()", notice.body)

    def test_a_good_response_is_processed_and_mails_nobody(self):
        self.scan(api_response(KNOWLES_STREET))

        self.assertEqual(DevelopmentPlan.objects.count(), 1)
        self.assertEqual(mail.outbox, [])

    def test_a_new_column_is_logged_but_does_not_stop_the_scan(self):
        extended = dict(KNOWLES_STREET, brand_new_column="whatever")

        with self.assertLogs("django", level="INFO") as logs:
            self.scan(api_response(extended))

        self.assertEqual(DevelopmentPlan.objects.count(), 1)
        self.assertEqual(mail.outbox, [])
        self.assertTrue(any("brand_new_column" in line for line in logs.output))
