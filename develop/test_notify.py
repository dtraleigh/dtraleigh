from datetime import timedelta
from unittest.mock import patch

from django.core import mail
from django.test import TestCase
from django.utils import timezone

from develop.management.commands.actions import create_new_discourse_post
from develop.management.commands.actions import reset_skipped_updates
from develop.management.commands.actions import send_skipped_update_digest
from develop.management.commands.notify import get_everything_that_changed
from develop.management.commands.scrape import update_zoning_if_changed
from develop.models import Subscriber
from develop.models import Zoning


class NotifyCosmeticChangeTestCase(TestCase):
    """The scrape-to-Discourse path, end to end, for a re-typed value.

    Z-50-25 was posted as an update whose only reported change was the
    zero-padding on a hearing date: "10/6/26" -> "10/06/26". Same hearing, same
    day. These tests pin down that such a scrape goes no further, while a real
    change still posts exactly as it did.
    """

    def setUp(self):
        self.zon = Zoning.objects.create(
            zpyear=2025,
            zpnum=50,
            location="2233 & 2321 Capital Blvd",
            location_url="https://maps.raleighnc.gov/z-50-25",
            status="City Council Public Hearing 10/6/26",
            plan_url="https://cityofraleigh0drupal.blob.core.usgovcloudapi.net/"
                     "drupal-prod/COR22/Z-050-25.pdf",
        )

        # Backdate both dates so this reads as a long-known case: created_date
        # puts the post on the "Existing ... Update" branch, and modified_date
        # leaves notify's last-hour window empty to start with.
        Zoning.objects.filter(pk=self.zon.pk).update(
            created_date=timezone.now() - timedelta(days=30),
            modified_date=timezone.now() - timedelta(days=30),
        )
        self.zon.refresh_from_db()

    def make_bot_subscriber(self):
        return Subscriber.objects.create(
            name="DevBot",
            email="bot@example.com",
            is_bot=True,
            topic_id=748,
            api_key="key",
        )

    def test_retyped_status_never_reaches_notify(self):
        update_zoning_if_changed(
            self.zon,
            "City Council Public Hearing 10/06/26",
            self.zon.plan_url,
            self.zon.location_url,
        )

        # notify works off modified_date, which the quiet sync leaves alone.
        self.assertEqual(get_everything_that_changed(), [])

        # Our copy still tracks what the city is publishing, though.
        self.zon.refresh_from_db()
        self.assertEqual(self.zon.status, "City Council Public Hearing 10/06/26")

    def test_real_status_change_does_reach_notify(self):
        update_zoning_if_changed(
            self.zon,
            "City Council Public Hearing 10/20/26",
            self.zon.plan_url,
            self.zon.location_url,
        )

        self.assertEqual(get_everything_that_changed(), [self.zon])

    @patch("develop.management.commands.actions.requests.request")
    def test_no_post_when_there_is_nothing_to_report(self, mock_request):
        """A single history record leaves nothing to diff against."""
        mock_request.return_value.json.return_value = {"slug": "the-raleigh-wire-service"}

        create_new_discourse_post(self.make_bot_subscriber(), self.zon)

        methods = [call.args[0] for call in mock_request.call_args_list]
        self.assertNotIn("POST", methods)

    @patch("develop.management.commands.actions.requests.request")
    def test_real_change_still_posts_the_updates_table(self, mock_request):
        mock_request.return_value.json.return_value = {"slug": "the-raleigh-wire-service"}

        self.zon.status = "City Council Public Hearing 10/20/26"
        self.zon.save()

        create_new_discourse_post(self.make_bot_subscriber(), self.zon)

        posts = [call for call in mock_request.call_args_list if call.args[0] == "POST"]
        self.assertEqual(len(posts), 1)

        body = posts[0].kwargs["data"]
        self.assertIn("### *Existing Zoning Request Update*", body)
        self.assertIn("## Z-50-25", body)
        self.assertIn("|Status|City Council Public Hearing 10/6/26|"
                      "City Council Public Hearing 10/20/26|", body)


class SkippedUpdateDigestTestCase(TestCase):
    """Admins get one digest per run covering everything that was not announced."""

    def setUp(self):
        Subscriber.objects.create(name="Leo", email="leo@dtraleigh.com", is_bot=False)
        Subscriber.objects.create(name="DevBot", email="bot@example.com", is_bot=True,
                                  topic_id=748, api_key="key")

        self.zon = self.make_zoning(50, "2233 & 2321 Capital Blvd")

        reset_skipped_updates()
        mail.outbox = []

    def make_zoning(self, zpnum, location):
        zon = Zoning.objects.create(
            zpyear=2025,
            zpnum=zpnum,
            location=location,
            location_url=f"https://maps.raleighnc.gov/z-{zpnum}-25",
            status="City Council Public Hearing 10/6/26",
            plan_url=f"https://example.com/Z-0{zpnum}-25.pdf",
        )

        Zoning.objects.filter(pk=zon.pk).update(
            created_date=timezone.now() - timedelta(days=30),
            modified_date=timezone.now() - timedelta(days=30),
        )
        zon.refresh_from_db()

        return zon

    def retype_status(self, zon):
        """Feed the scrape a status that differs only in its zero-padding."""
        return update_zoning_if_changed(
            zon,
            "City Council Public Hearing 10/06/26",
            zon.plan_url,
            zon.location_url,
        )

    def test_nothing_is_mailed_until_the_digest_is_sent(self):
        self.retype_status(self.zon)

        self.assertEqual(mail.outbox, [])

        send_skipped_update_digest()

        self.assertEqual(len(mail.outbox), 1)

    def test_the_digest_names_the_item_the_reason_and_the_values(self):
        self.retype_status(self.zon)
        send_skipped_update_digest()

        notice = mail.outbox[0]

        # Goes to the humans, not the bot subscribers.
        self.assertEqual(notice.to, ["leo@dtraleigh.com"])
        self.assertIn("1 update skipped", notice.subject)
        self.assertIn("no significant change", notice.subject)

        self.assertIn("Zoning Request 'Zone - 50 (2025)'", notice.body)
        self.assertIn("Reason:", notice.body)
        self.assertIn("how the value was typed", notice.body)
        self.assertIn("Field: status", notice.body)
        self.assertIn("City Council Public Hearing 10/6/26", notice.body)
        self.assertIn("City Council Public Hearing 10/06/26", notice.body)
        self.assertIn("city council public hearing 10/06/2026", notice.body)
        self.assertIn("develop/normalize.py", notice.body)

    def test_many_skips_become_one_email(self):
        """The whole point of batching: a table-wide reformat is one message."""
        others = [self.make_zoning(num, f"{str(num)} Fake St") for num in (51, 52, 53)]

        for zon in [self.zon] + others:
            self.retype_status(zon)

        send_skipped_update_digest()

        self.assertEqual(len(mail.outbox), 1)

        notice = mail.outbox[0]
        self.assertIn("4 updates skipped", notice.subject)

        for zpnum in (50, 51, 52, 53):
            self.assertIn(f"Zone - {str(zpnum)} (2025)", notice.body)

    def test_whitespace_is_visible_in_the_digest(self):
        """repr'd values, so an &nbsp; the city left behind can actually be seen."""
        update_zoning_if_changed(
            self.zon,
            "City Council Public Hearing 10/6/26\xa0",
            self.zon.plan_url,
            self.zon.location_url,
        )
        send_skipped_update_digest()

        self.assertIn("\\xa0", mail.outbox[0].body)

    def test_identical_values_mail_nobody(self):
        update_zoning_if_changed(self.zon, self.zon.status, self.zon.plan_url,
                                 self.zon.location_url)
        send_skipped_update_digest()

        self.assertEqual(mail.outbox, [])

    def test_a_real_change_mails_nobody(self):
        """A real change is announced on Discourse, so there is nothing to explain."""
        update_zoning_if_changed(self.zon, "City Council Public Hearing 10/20/26",
                                 self.zon.plan_url, self.zon.location_url)
        send_skipped_update_digest()

        self.assertEqual(mail.outbox, [])

    def test_the_digest_drains_so_a_later_run_does_not_repeat_it(self):
        self.retype_status(self.zon)
        send_skipped_update_digest()
        self.assertEqual(len(mail.outbox), 1)

        send_skipped_update_digest()
        self.assertEqual(len(mail.outbox), 1)

    @patch("develop.management.commands.actions.requests.request")
    def test_notify_backstop_explains_a_missing_previous_record(self, mock_request):
        mock_request.return_value.json.return_value = {"slug": "the-raleigh-wire-service"}

        create_new_discourse_post(Subscriber.objects.get(name="DevBot"), self.zon)
        send_skipped_update_digest()

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("only one history record", mail.outbox[0].body)

    @patch("develop.management.commands.actions.requests.request")
    def test_notify_backstop_explains_a_cosmetic_only_history(self, mock_request):
        mock_request.return_value.json.return_value = {"slug": "the-raleigh-wire-service"}

        self.zon.status = "CITY COUNCIL PUBLIC HEARING 10/06/26"
        self.zon.save()

        create_new_discourse_post(Subscriber.objects.get(name="DevBot"), self.zon)
        send_skipped_update_digest()

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("only in how it was typed", mail.outbox[0].body)

    @patch("develop.management.commands.actions.send_email_notice")
    def test_a_failing_mail_server_does_not_fail_the_run(self, mock_send):
        """The digest is informational; a healthy scrape must stay healthy."""
        mock_send.side_effect = Exception("SMTP is down")

        result = self.retype_status(self.zon)
        send_skipped_update_digest()

        self.assertFalse(result)

        # The value still landed, despite the digest blowing up.
        self.zon.refresh_from_db()
        self.assertEqual(self.zon.status, "City Council Public Hearing 10/06/26")
