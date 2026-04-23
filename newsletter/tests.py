import json
import time
import uuid
from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone

from .forms import SubscribeForm
from .models import SendLog, SentPost, Subscriber


class SubscribeFormTest(SimpleTestCase):
    """Tests for the SubscribeForm (no DB needed)."""

    def test_valid_email_passes_validation(self):
        form = SubscribeForm(data={"email": "test@example.com", "website": ""})
        self.assertTrue(form.is_valid())

    def test_invalid_email_fails_validation(self):
        form = SubscribeForm(data={"email": "not-an-email", "website": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_empty_email_fails_validation(self):
        form = SubscribeForm(data={"email": "", "website": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_honeypot_field_not_required(self):
        form = SubscribeForm(data={"email": "test@example.com"})
        self.assertTrue(form.is_valid())

    def test_email_normalized_to_lowercase(self):
        form = SubscribeForm(data={"email": "Test@EXAMPLE.com", "website": ""})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["email"], "test@example.com")


@override_settings(RATELIMIT_ENABLE=False)
class SubscribeViewTest(TestCase):
    """Tests for the subscribe view."""

    def test_get_returns_200_with_form(self):
        response = self.client.get("/newsletter/subscribe/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "email")

    @patch("newsletter.views.send_confirmation_email")
    def test_post_valid_email_creates_subscriber_and_sends_email(self, mock_send):
        response = self.client.post("/newsletter/subscribe/", {"email": "new@example.com", "website": ""})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "newsletter/subscribe_success.html")
        subscriber = Subscriber.objects.get(email="new@example.com")
        self.assertEqual(subscriber.status, Subscriber.STATUS_UNCONFIRMED)
        mock_send.assert_called_once_with(subscriber)

    @patch("newsletter.views.send_confirmation_email")
    def test_post_honeypot_filled_creates_no_subscriber(self, mock_send):
        response = self.client.post("/newsletter/subscribe/", {"email": "bot@example.com", "website": "http://spam.com"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "newsletter/subscribe_success.html")
        self.assertFalse(Subscriber.objects.filter(email="bot@example.com").exists())
        mock_send.assert_not_called()

    @patch("newsletter.views.send_confirmation_email")
    def test_post_invalid_email_rerenders_form_with_errors(self, mock_send):
        response = self.client.post("/newsletter/subscribe/", {"email": "bad", "website": ""})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "newsletter/subscribe.html")
        self.assertContains(response, "form")
        mock_send.assert_not_called()

    @patch("newsletter.views.send_confirmation_email")
    def test_post_already_confirmed_shows_success_no_email(self, mock_send):
        Subscriber.objects.create(email="confirmed@example.com", status=Subscriber.STATUS_CONFIRMED)
        response = self.client.post("/newsletter/subscribe/", {"email": "confirmed@example.com", "website": ""})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "newsletter/subscribe_success.html")
        mock_send.assert_not_called()

    @patch("newsletter.views.send_confirmation_email")
    def test_post_unconfirmed_resets_token_and_resends(self, mock_send):
        subscriber = Subscriber.objects.create(email="unconf@example.com", status=Subscriber.STATUS_UNCONFIRMED)
        old_token = subscriber.token
        self.client.post("/newsletter/subscribe/", {"email": "unconf@example.com", "website": ""})
        subscriber.refresh_from_db()
        self.assertNotEqual(subscriber.token, old_token)
        mock_send.assert_called_once_with(subscriber)

    @patch("newsletter.views.send_confirmation_email")
    def test_post_unsubscribed_resets_to_unconfirmed(self, mock_send):
        subscriber = Subscriber.objects.create(
            email="unsub@example.com",
            status=Subscriber.STATUS_UNSUBSCRIBED,
            unsubscribed_at="2025-01-01T00:00:00Z",
        )
        old_token = subscriber.token
        self.client.post("/newsletter/subscribe/", {"email": "unsub@example.com", "website": ""})
        subscriber.refresh_from_db()
        self.assertEqual(subscriber.status, Subscriber.STATUS_UNCONFIRMED)
        self.assertNotEqual(subscriber.token, old_token)
        self.assertIsNone(subscriber.unsubscribed_at)
        mock_send.assert_called_once_with(subscriber)

    @patch("newsletter.views.send_confirmation_email")
    def test_post_bounced_shows_bounced_template_no_email(self, mock_send):
        Subscriber.objects.create(email="bounced@example.com", status=Subscriber.STATUS_BOUNCED)
        response = self.client.post("/newsletter/subscribe/", {"email": "bounced@example.com", "website": ""})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "newsletter/subscribe_bounced.html")
        mock_send.assert_not_called()


class ConfirmViewTest(TestCase):
    """Tests for the confirm view."""

    def test_valid_token_unconfirmed_sets_confirmed(self):
        subscriber = Subscriber.objects.create(email="test@example.com", status=Subscriber.STATUS_UNCONFIRMED)
        response = self.client.get(f"/newsletter/confirm/{subscriber.token}/")
        self.assertTemplateUsed(response, "newsletter/confirm_success.html")
        subscriber.refresh_from_db()
        self.assertEqual(subscriber.status, Subscriber.STATUS_CONFIRMED)
        self.assertIsNotNone(subscriber.confirmed_at)

    def test_valid_token_already_confirmed_shows_already_page(self):
        subscriber = Subscriber.objects.create(email="test@example.com", status=Subscriber.STATUS_CONFIRMED)
        response = self.client.get(f"/newsletter/confirm/{subscriber.token}/")
        self.assertTemplateUsed(response, "newsletter/confirm_already.html")

    def test_valid_token_unsubscribed_shows_invalid(self):
        subscriber = Subscriber.objects.create(email="test@example.com", status=Subscriber.STATUS_UNSUBSCRIBED)
        response = self.client.get(f"/newsletter/confirm/{subscriber.token}/")
        self.assertTemplateUsed(response, "newsletter/confirm_invalid.html")

    def test_valid_token_bounced_shows_invalid(self):
        subscriber = Subscriber.objects.create(email="test@example.com", status=Subscriber.STATUS_BOUNCED)
        response = self.client.get(f"/newsletter/confirm/{subscriber.token}/")
        self.assertTemplateUsed(response, "newsletter/confirm_invalid.html")

    def test_invalid_token_shows_invalid(self):
        fake_token = uuid.uuid4()
        response = self.client.get(f"/newsletter/confirm/{fake_token}/")
        self.assertTemplateUsed(response, "newsletter/confirm_invalid.html")


class UnsubscribeViewTest(TestCase):
    """Tests for the unsubscribe view."""

    def test_get_shows_confirmation_page_with_email(self):
        subscriber = Subscriber.objects.create(email="test@example.com", status=Subscriber.STATUS_CONFIRMED)
        response = self.client.get(f"/newsletter/unsubscribe/{subscriber.token}/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "newsletter/unsubscribe_confirm.html")
        self.assertContains(response, subscriber.email)

    def test_post_sets_unsubscribed(self):
        subscriber = Subscriber.objects.create(email="test@example.com", status=Subscriber.STATUS_CONFIRMED)
        response = self.client.post(f"/newsletter/unsubscribe/{subscriber.token}/")
        self.assertTemplateUsed(response, "newsletter/unsubscribe_success.html")
        subscriber.refresh_from_db()
        self.assertEqual(subscriber.status, Subscriber.STATUS_UNSUBSCRIBED)
        self.assertIsNotNone(subscriber.unsubscribed_at)

    def test_post_no_form_data_one_click_unsubscribe(self):
        subscriber = Subscriber.objects.create(email="test@example.com", status=Subscriber.STATUS_CONFIRMED)
        response = self.client.post(
            f"/newsletter/unsubscribe/{subscriber.token}/",
            content_type="application/x-www-form-urlencoded",
        )
        self.assertTemplateUsed(response, "newsletter/unsubscribe_success.html")
        subscriber.refresh_from_db()
        self.assertEqual(subscriber.status, Subscriber.STATUS_UNSUBSCRIBED)

    def test_invalid_token_shows_invalid(self):
        fake_token = uuid.uuid4()
        response = self.client.get(f"/newsletter/unsubscribe/{fake_token}/")
        self.assertTemplateUsed(response, "newsletter/confirm_invalid.html")


class SendConfirmationEmailTest(TestCase):
    """Tests for the send_confirmation_email helper."""

    @patch("newsletter.email.send_mail")
    def test_django_backend_calls_send_mail_and_logs(self, mock_send_mail):
        subscriber = Subscriber.objects.create(email="test@example.com")
        with self.settings(NEWSLETTER_USE_SES=False, NEWSLETTER_BASE_URL="https://apps.dtraleigh.com",
                           NEWSLETTER_FROM_EMAIL="newsletter@dtraleigh.com"):
            from newsletter.email import send_confirmation_email
            send_confirmation_email(subscriber)

        mock_send_mail.assert_called_once()
        call_kwargs = mock_send_mail.call_args
        self.assertEqual(call_kwargs[1]["recipient_list"], [subscriber.email])
        log = SendLog.objects.get(subscriber=subscriber)
        self.assertEqual(log.event_type, SendLog.EVENT_CONFIRMATION_SENT)

    @patch("newsletter.email.send_mail", side_effect=Exception("SMTP error"))
    def test_send_failure_creates_error_log_and_reraises(self, mock_send_mail):
        subscriber = Subscriber.objects.create(email="test@example.com")
        with self.settings(NEWSLETTER_USE_SES=False, NEWSLETTER_BASE_URL="https://apps.dtraleigh.com",
                           NEWSLETTER_FROM_EMAIL="newsletter@dtraleigh.com"):
            from newsletter.email import send_confirmation_email
            with self.assertRaises(Exception):
                send_confirmation_email(subscriber)

        log = SendLog.objects.get(subscriber=subscriber)
        self.assertEqual(log.event_type, SendLog.EVENT_ERROR)
        self.assertIn("SMTP error", log.detail)

    @patch("newsletter.email.send_mail")
    def test_confirmation_url_contains_token(self, mock_send_mail):
        subscriber = Subscriber.objects.create(email="test@example.com")
        with self.settings(NEWSLETTER_USE_SES=False, NEWSLETTER_BASE_URL="https://apps.dtraleigh.com",
                           NEWSLETTER_FROM_EMAIL="newsletter@dtraleigh.com"):
            from newsletter.email import send_confirmation_email
            send_confirmation_email(subscriber)

        call_kwargs = mock_send_mail.call_args
        # The token should appear in the text body (message kwarg)
        self.assertIn(str(subscriber.token), call_kwargs[1]["message"])


class SendNewsletterTest(TestCase):
    """Tests for the send_newsletter helper."""

    def setUp(self):
        self.confirmed1 = Subscriber.objects.create(email="c1@example.com", status=Subscriber.STATUS_CONFIRMED)
        self.confirmed2 = Subscriber.objects.create(email="c2@example.com", status=Subscriber.STATUS_CONFIRMED)
        Subscriber.objects.create(email="unconf@example.com", status=Subscriber.STATUS_UNCONFIRMED)
        Subscriber.objects.create(email="unsub@example.com", status=Subscriber.STATUS_UNSUBSCRIBED)
        Subscriber.objects.create(email="bounced@example.com", status=Subscriber.STATUS_BOUNCED)
        self.sent_post = SentPost.objects.create(guid="test-guid", title="Test Post")

    @patch("newsletter.email._send_django_email")
    def test_sends_only_to_confirmed_subscribers(self, mock_send):
        with self.settings(NEWSLETTER_USE_SES=False, NEWSLETTER_BASE_URL="https://apps.dtraleigh.com",
                           NEWSLETTER_FROM_EMAIL="newsletter@dtraleigh.com",
                           NEWSLETTER_MAILING_ADDRESS="Raleigh, NC"):
            from newsletter.email import send_newsletter
            count = send_newsletter("Subject", "<p>HTML</p>", "Text", "https://dtraleigh.com/post", self.sent_post)

        self.assertEqual(count, 2)
        self.assertEqual(mock_send.call_count, 2)
        sent_emails = [call[0][1] for call in mock_send.call_args_list]
        self.assertIn("c1@example.com", sent_emails)
        self.assertIn("c2@example.com", sent_emails)

    @patch("newsletter.email._send_django_email")
    def test_creates_send_logs_per_subscriber(self, mock_send):
        with self.settings(NEWSLETTER_USE_SES=False, NEWSLETTER_BASE_URL="https://apps.dtraleigh.com",
                           NEWSLETTER_FROM_EMAIL="newsletter@dtraleigh.com",
                           NEWSLETTER_MAILING_ADDRESS="Raleigh, NC"):
            from newsletter.email import send_newsletter
            send_newsletter("Subject", "<p>HTML</p>", "Text", "https://dtraleigh.com/post", self.sent_post)

        logs = SendLog.objects.filter(event_type=SendLog.EVENT_NEWSLETTER_SENT, sent_post=self.sent_post)
        self.assertEqual(logs.count(), 2)

    @patch("newsletter.email._send_django_email")
    def test_partial_failure_logs_error_and_continues(self, mock_send):
        mock_send.side_effect = [Exception("fail"), None]
        with self.settings(NEWSLETTER_USE_SES=False, NEWSLETTER_BASE_URL="https://apps.dtraleigh.com",
                           NEWSLETTER_FROM_EMAIL="newsletter@dtraleigh.com",
                           NEWSLETTER_MAILING_ADDRESS="Raleigh, NC"):
            from newsletter.email import send_newsletter
            count = send_newsletter("Subject", "<p>HTML</p>", "Text", "https://dtraleigh.com/post", self.sent_post)

        self.assertEqual(count, 1)
        error_logs = SendLog.objects.filter(event_type=SendLog.EVENT_ERROR, sent_post=self.sent_post)
        self.assertEqual(error_logs.count(), 1)
        success_logs = SendLog.objects.filter(event_type=SendLog.EVENT_NEWSLETTER_SENT, sent_post=self.sent_post)
        self.assertEqual(success_logs.count(), 1)

    @patch("newsletter.email._send_django_email")
    def test_rendered_email_contains_unsubscribe_url(self, mock_send):
        with self.settings(NEWSLETTER_USE_SES=False, NEWSLETTER_BASE_URL="https://apps.dtraleigh.com",
                           NEWSLETTER_FROM_EMAIL="newsletter@dtraleigh.com",
                           NEWSLETTER_MAILING_ADDRESS="Raleigh, NC"):
            from newsletter.email import send_newsletter
            send_newsletter("Subject", "<p>HTML</p>", "Text", "https://dtraleigh.com/post", self.sent_post)

        # Check that unsubscribe URL with token was passed for each subscriber
        for call in mock_send.call_args_list:
            args = call[0]
            unsubscribe_url = args[5]  # 6th positional arg is unsubscribe_url
            self.assertIn("/newsletter/unsubscribe/", unsubscribe_url)

    @patch("newsletter.email._send_django_email")
    def test_rendered_email_contains_post_url_and_mailing_address(self, mock_send):
        with self.settings(NEWSLETTER_USE_SES=False, NEWSLETTER_BASE_URL="https://apps.dtraleigh.com",
                           NEWSLETTER_FROM_EMAIL="newsletter@dtraleigh.com",
                           NEWSLETTER_MAILING_ADDRESS="DTRaleigh, Raleigh, NC"):
            from newsletter.email import send_newsletter
            send_newsletter("Subject", "<p>HTML</p>", "Text", "https://dtraleigh.com/post", self.sent_post)

        # The rendered HTML (3rd arg) should contain the post URL and mailing address
        call_args = mock_send.call_args_list[0][0]
        rendered_html = call_args[3]  # 4th positional arg is html_body
        self.assertIn("https://dtraleigh.com/post", rendered_html)
        self.assertIn("DTRaleigh, Raleigh, NC", rendered_html)


def _make_feed_entry(guid="https://dtraleigh.com/?p=100", title="Test Post",
                     link="https://dtraleigh.com/test-post/",
                     html_content="<p>Hello world</p>",
                     summary="Hello world summary",
                     published_parsed=None):
    """Create a mock feedparser entry."""
    entry = MagicMock()
    entry.get = lambda key, default="": {
        "id": guid,
        "title": title,
        "link": link,
        "summary": summary,
        "published_parsed": published_parsed or time.strptime("2026-03-10", "%Y-%m-%d"),
    }.get(key, default)
    entry.id = guid
    entry.title = title
    entry.link = link
    entry.summary = summary
    entry.content = [{"value": html_content}]
    entry.published_parsed = published_parsed or time.strptime("2026-03-10", "%Y-%m-%d")
    # Make hasattr(entry, "content") work correctly
    type(entry).content = property(lambda self: [{"value": html_content}])
    return entry


def _make_feed(*entries):
    """Create a mock feedparser feed result."""
    feed = MagicMock()
    feed.bozo = False
    feed.entries = list(entries)
    return feed


@override_settings(
    NEWSLETTER_USE_SES=False,
    NEWSLETTER_BASE_URL="https://apps.dtraleigh.com",
    NEWSLETTER_FROM_EMAIL="newsletter@dtraleigh.com",
    NEWSLETTER_MAILING_ADDRESS="Raleigh, NC",
    NEWSLETTER_SEND_ALL_NEW=True,
)
class SendNewsletterCommandTest(TestCase):
    """Tests for the send_newsletter management command."""

    @patch("newsletter.management.commands.send_newsletter.send_newsletter")
    @patch("newsletter.management.commands.send_newsletter.feedparser.parse")
    def test_seed_creates_sent_posts_without_sending(self, mock_parse, mock_send):
        entry1 = _make_feed_entry(guid="guid-1", title="Post 1")
        entry2 = _make_feed_entry(guid="guid-2", title="Post 2")
        mock_parse.return_value = _make_feed(entry1, entry2)

        from django.core.management import call_command
        call_command("send_newsletter", "--seed")

        self.assertEqual(SentPost.objects.count(), 2)
        self.assertTrue(SentPost.objects.filter(guid="guid-1").exists())
        self.assertTrue(SentPost.objects.filter(guid="guid-2").exists())
        # recipient_count should be 0 for seeded posts, and seeded flag set
        for sp in SentPost.objects.all():
            self.assertEqual(sp.recipient_count, 0)
            self.assertTrue(sp.seeded)
        mock_send.assert_not_called()

    @patch("newsletter.management.commands.send_newsletter.send_newsletter")
    @patch("newsletter.management.commands.send_newsletter.feedparser.parse")
    def test_seed_skips_already_existing_guids(self, mock_parse, mock_send):
        SentPost.objects.create(guid="guid-1", title="Existing Post", recipient_count=5)
        entry1 = _make_feed_entry(guid="guid-1", title="Post 1")
        entry2 = _make_feed_entry(guid="guid-2", title="Post 2")
        mock_parse.return_value = _make_feed(entry1, entry2)

        from django.core.management import call_command
        call_command("send_newsletter", "--seed")

        self.assertEqual(SentPost.objects.count(), 2)
        # Existing post should not be modified
        existing = SentPost.objects.get(guid="guid-1")
        self.assertEqual(existing.recipient_count, 5)

    @patch("newsletter.management.commands.send_newsletter.send_newsletter")
    @patch("newsletter.management.commands.send_newsletter.feedparser.parse")
    def test_new_entry_creates_sent_post_and_sends(self, mock_parse, mock_send):
        mock_send.return_value = 3
        entry = _make_feed_entry(guid="guid-new", title="New Post",
                                 html_content="<p>Content</p>",
                                 link="https://dtraleigh.com/new-post/")
        mock_parse.return_value = _make_feed(entry)

        from django.core.management import call_command
        call_command("send_newsletter")

        sent_post = SentPost.objects.get(guid="guid-new")
        self.assertEqual(sent_post.title, "New Post")
        self.assertEqual(sent_post.recipient_count, 3)
        mock_send.assert_called_once()
        call_args = mock_send.call_args[0]
        self.assertEqual(call_args[0], "DTRaleigh: New Post")  # subject
        self.assertIn("<p>Content</p>", call_args[1])  # html_content (preview)
        self.assertIn("Content", call_args[2])  # text_content (stripped)
        self.assertNotIn("<p>", call_args[2])  # no HTML tags in text
        self.assertEqual(call_args[3], "https://dtraleigh.com/new-post/")  # post_url

    @patch("newsletter.management.commands.send_newsletter.send_newsletter")
    @patch("newsletter.management.commands.send_newsletter.feedparser.parse")
    def test_already_sent_guid_is_skipped(self, mock_parse, mock_send):
        SentPost.objects.create(guid="guid-1", title="Already Sent", recipient_count=5)
        entry = _make_feed_entry(guid="guid-1", title="Already Sent")
        mock_parse.return_value = _make_feed(entry)

        from django.core.management import call_command
        call_command("send_newsletter")

        mock_send.assert_not_called()

    @patch("newsletter.management.commands.send_newsletter.send_newsletter")
    @patch("newsletter.management.commands.send_newsletter.feedparser.parse")
    def test_failed_previous_attempt_is_retried(self, mock_parse, mock_send):
        mock_send.return_value = 2
        failed_post = SentPost.objects.create(guid="guid-failed", title="Failed Post", recipient_count=0)
        entry = _make_feed_entry(guid="guid-failed", title="Failed Post")
        mock_parse.return_value = _make_feed(entry)

        from django.core.management import call_command
        call_command("send_newsletter")

        mock_send.assert_called_once()
        # Should reuse the existing SentPost, not create a new one
        self.assertEqual(SentPost.objects.filter(guid="guid-failed").count(), 1)
        failed_post.refresh_from_db()
        self.assertEqual(failed_post.recipient_count, 2)

    @patch("newsletter.management.commands.send_newsletter.send_newsletter")
    @patch("newsletter.management.commands.send_newsletter.feedparser.parse")
    def test_seeded_post_is_not_retried(self, mock_parse, mock_send):
        # A row with recipient_count=0 but seeded=True must NOT be treated as
        # a failed-send retry. Without this guard, --seed followed by adding
        # confirmed subscribers within 24h would mail every seeded post.
        SentPost.objects.create(
            guid="guid-seeded", title="Seeded Post",
            recipient_count=0, seeded=True,
        )
        entry = _make_feed_entry(guid="guid-seeded", title="Seeded Post")
        mock_parse.return_value = _make_feed(entry)

        from django.core.management import call_command
        call_command("send_newsletter")

        mock_send.assert_not_called()

    @patch("newsletter.management.commands.send_newsletter.send_newsletter")
    @patch("newsletter.management.commands.send_newsletter.feedparser.parse")
    def test_seeded_post_past_cutoff_is_not_abandoned(self, mock_parse, mock_send):
        # Seeded rows older than 24h must not trigger the "abandoning" warning
        # path either — they should be silently ignored as already-sent.
        seeded_post = SentPost.objects.create(
            guid="guid-old-seed", title="Old Seed",
            recipient_count=0, seeded=True,
        )
        SentPost.objects.filter(pk=seeded_post.pk).update(
            sent_at=timezone.now() - timedelta(hours=25)
        )
        entry = _make_feed_entry(guid="guid-old-seed", title="Old Seed")
        mock_parse.return_value = _make_feed(entry)

        from django.core.management import call_command
        with self.assertNoLogs("newsletter.management.commands.send_newsletter", level="WARNING"):
            call_command("send_newsletter")

        mock_send.assert_not_called()

    @patch("newsletter.management.commands.send_newsletter.send_newsletter")
    @patch("newsletter.management.commands.send_newsletter.feedparser.parse")
    def test_seed_does_not_flip_existing_failed_send_to_seeded(self, mock_parse, mock_send):
        # A pre-existing failed-send row (count=0, seeded=False) must NOT be
        # silently converted into a seed marker by re-running --seed. The
        # failed-send retry path should remain intact.
        failed_post = SentPost.objects.create(
            guid="guid-failed", title="Failed Post", recipient_count=0
        )
        entry = _make_feed_entry(guid="guid-failed", title="Failed Post")
        mock_parse.return_value = _make_feed(entry)

        from django.core.management import call_command
        call_command("send_newsletter", "--seed")

        failed_post.refresh_from_db()
        self.assertFalse(failed_post.seeded)

    @patch("newsletter.management.commands.send_newsletter.send_newsletter")
    @patch("newsletter.management.commands.send_newsletter.feedparser.parse")
    def test_multiple_entries_sent_oldest_first(self, mock_parse, mock_send):
        mock_send.return_value = 1
        older = _make_feed_entry(guid="guid-old", title="Old Post",
                                 published_parsed=time.strptime("2026-03-01", "%Y-%m-%d"))
        newer = _make_feed_entry(guid="guid-new", title="New Post",
                                 published_parsed=time.strptime("2026-03-10", "%Y-%m-%d"))
        # Feed returns newer first (typical RSS order)
        mock_parse.return_value = _make_feed(newer, older)

        from django.core.management import call_command
        call_command("send_newsletter")

        self.assertEqual(mock_send.call_count, 2)
        # First call should be the older post
        first_subject = mock_send.call_args_list[0][0][0]
        second_subject = mock_send.call_args_list[1][0][0]
        self.assertEqual(first_subject, "DTRaleigh: Old Post")
        self.assertEqual(second_subject, "DTRaleigh: New Post")

    @patch("newsletter.management.commands.send_newsletter.send_newsletter")
    @patch("newsletter.management.commands.send_newsletter.feedparser.parse")
    @override_settings(NEWSLETTER_SEND_ALL_NEW=False)
    def test_send_all_new_false_sends_only_most_recent(self, mock_parse, mock_send):
        mock_send.return_value = 1
        older = _make_feed_entry(guid="guid-old", title="Old Post",
                                 published_parsed=time.strptime("2026-03-01", "%Y-%m-%d"))
        newer = _make_feed_entry(guid="guid-new", title="New Post",
                                 published_parsed=time.strptime("2026-03-10", "%Y-%m-%d"))
        mock_parse.return_value = _make_feed(newer, older)

        from django.core.management import call_command
        call_command("send_newsletter")

        mock_send.assert_called_once()
        sent_subject = mock_send.call_args[0][0]
        self.assertEqual(sent_subject, "DTRaleigh: New Post")

    @patch("newsletter.management.commands.send_newsletter.send_newsletter")
    @patch("newsletter.management.commands.send_newsletter.feedparser.parse")
    def test_no_new_entries_does_nothing(self, mock_parse, mock_send):
        SentPost.objects.create(guid="guid-1", title="Sent", recipient_count=5)
        entry = _make_feed_entry(guid="guid-1", title="Sent")
        mock_parse.return_value = _make_feed(entry)

        from django.core.management import call_command
        call_command("send_newsletter")

        mock_send.assert_not_called()

    @patch("newsletter.management.commands.send_newsletter.send_newsletter")
    @patch("newsletter.management.commands.send_newsletter.feedparser.parse")
    def test_content_encoded_preferred_over_summary(self, mock_parse, mock_send):
        mock_send.return_value = 1
        entry = _make_feed_entry(guid="guid-1", title="Post",
                                 html_content="<p>Full content</p>",
                                 summary="Just a summary")
        mock_parse.return_value = _make_feed(entry)

        from django.core.management import call_command
        call_command("send_newsletter")

        html_arg = mock_send.call_args[0][1]
        self.assertIn("Full content", html_arg)
        self.assertNotIn("Just a summary", html_arg)

    @patch("newsletter.management.commands.send_newsletter.send_newsletter")
    @patch("newsletter.management.commands.send_newsletter.feedparser.parse")
    def test_falls_back_to_summary_when_no_content(self, mock_parse, mock_send):
        mock_send.return_value = 1
        entry = _make_feed_entry(guid="guid-1", title="Post", summary="Summary text")
        # Remove the content attribute to simulate no content:encoded
        del type(entry).content
        entry.content = None
        mock_parse.return_value = _make_feed(entry)

        from django.core.management import call_command
        call_command("send_newsletter")

        html_arg = mock_send.call_args[0][1]
        self.assertIn("Summary text", html_arg)

    @patch("newsletter.management.commands.send_newsletter.send_newsletter")
    @patch("newsletter.management.commands.send_newsletter.feedparser.parse")
    def test_plain_text_has_tags_stripped(self, mock_parse, mock_send):
        mock_send.return_value = 1
        entry = _make_feed_entry(guid="guid-1", title="Post",
                                 html_content="<p>Hello <strong>world</strong></p>")
        mock_parse.return_value = _make_feed(entry)

        from django.core.management import call_command
        call_command("send_newsletter")

        text_arg = mock_send.call_args[0][2]
        self.assertIn("Hello", text_arg)
        self.assertIn("world", text_arg)
        self.assertNotIn("<p>", text_arg)
        self.assertNotIn("<strong>", text_arg)

    @patch("newsletter.management.commands.send_newsletter.send_newsletter")
    @patch("newsletter.management.commands.send_newsletter.feedparser.parse")
    def test_plain_text_decodes_html_entities(self, mock_parse, mock_send):
        # WordPress RSS content:encoded contains entities like &#8217; for
        # curly apostrophes. strip_tags alone leaves them literal in plain
        # text; the command must also html.unescape() the result.
        mock_send.return_value = 1
        entry = _make_feed_entry(
            guid="guid-1", title="Post",
            html_content="<p>It&#8217;s a test &amp; an example</p>",
        )
        mock_parse.return_value = _make_feed(entry)

        from django.core.management import call_command
        call_command("send_newsletter")

        text_arg = mock_send.call_args[0][2]
        self.assertIn("It\u2019s a test & an example", text_arg)
        self.assertNotIn("&#8217;", text_arg)
        self.assertNotIn("&amp;", text_arg)

    @patch("newsletter.management.commands.send_newsletter.send_newsletter")
    @patch("newsletter.management.commands.send_newsletter.feedparser.parse")
    def test_retry_abandoned_after_cutoff(self, mock_parse, mock_send):
        failed_post = SentPost.objects.create(guid="guid-old-fail", title="Old Failure", recipient_count=0)
        # Backdate sent_at to exceed the 24h cutoff
        SentPost.objects.filter(pk=failed_post.pk).update(sent_at=timezone.now() - timedelta(hours=25))
        entry = _make_feed_entry(guid="guid-old-fail", title="Old Failure")
        mock_parse.return_value = _make_feed(entry)

        from django.core.management import call_command
        call_command("send_newsletter")

        mock_send.assert_not_called()
        failed_post.refresh_from_db()
        self.assertEqual(failed_post.recipient_count, 0)

    @patch("newsletter.management.commands.send_newsletter.send_newsletter")
    @patch("newsletter.management.commands.send_newsletter.feedparser.parse")
    def test_youtube_iframe_converted_to_thumbnail(self, mock_parse, mock_send):
        mock_send.return_value = 1
        html_content = (
            '<figure class="wp-block-embed is-type-video wp-block-embed-youtube">'
            '<div class="wp-block-embed__wrapper">'
            '<iframe src="https://www.youtube.com/embed/abc123XYZ" '
            'width="730" height="411"></iframe>'
            '</div></figure>'
            '<p>Some text here.</p>'
        )
        entry = _make_feed_entry(guid="guid-yt", title="YT Post",
                                 html_content=html_content)
        mock_parse.return_value = _make_feed(entry)

        from django.core.management import call_command
        call_command("send_newsletter")

        html_arg = mock_send.call_args[0][1]
        self.assertIn("img.youtube.com/vi/abc123XYZ/hqdefault.jpg", html_arg)
        self.assertIn("youtube.com/watch?v=abc123XYZ", html_arg)
        self.assertNotIn("<iframe", html_arg)
        self.assertIn("Some text here.", html_arg)

    @patch("newsletter.management.commands.send_newsletter.send_newsletter")
    @patch("newsletter.management.commands.send_newsletter.feedparser.parse")
    def test_image_takes_priority_over_youtube_iframe(self, mock_parse, mock_send):
        mock_send.return_value = 1
        html_content = (
            '<img src="https://example.com/photo.jpg" />'
            '<iframe src="https://www.youtube.com/embed/abc123XYZ"></iframe>'
            '<p>Text content.</p>'
        )
        entry = _make_feed_entry(guid="guid-both", title="Both Post",
                                 html_content=html_content)
        mock_parse.return_value = _make_feed(entry)

        from django.core.management import call_command
        call_command("send_newsletter")

        html_arg = mock_send.call_args[0][1]
        self.assertIn("example.com/photo.jpg", html_arg)
        self.assertNotIn("img.youtube.com", html_arg)

    @patch("newsletter.management.commands.send_newsletter.send_newsletter")
    @patch("newsletter.management.commands.send_newsletter.feedparser.parse")
    def test_no_image_no_youtube_returns_paragraph(self, mock_parse, mock_send):
        mock_send.return_value = 1
        html_content = "<p>Just a paragraph.</p>"
        entry = _make_feed_entry(guid="guid-plain", title="Plain Post",
                                 html_content=html_content)
        mock_parse.return_value = _make_feed(entry)

        from django.core.management import call_command
        call_command("send_newsletter")

        html_arg = mock_send.call_args[0][1]
        self.assertIn("Just a paragraph.", html_arg)
        self.assertNotIn("<img", html_arg)


def _make_sns_payload(message_type, message_body, sns_type="Notification"):
    """Build a minimal SNS payload dict for testing."""
    return {
        "Type": sns_type,
        "MessageId": str(uuid.uuid4()),
        "TopicArn": "arn:aws:sns:us-east-1:123456789:test-topic",
        "Message": json.dumps(message_body) if isinstance(message_body, dict) else message_body,
        "Timestamp": "2026-03-19T12:00:00.000Z",
        "SignatureVersion": "1",
        "Signature": "dGVzdA==",
        "SigningCertURL": "https://sns.us-east-1.amazonaws.com/test.pem",
    }


def _make_bounce_payload(email_address):
    """Build an SNS payload containing an SES bounce notification."""
    return _make_sns_payload(
        message_type="Notification",
        message_body={
            "notificationType": "Bounce",
            "bounce": {
                "bouncedRecipients": [{"emailAddress": email_address}],
                "bounceType": "Permanent",
            },
        },
    )


def _make_complaint_payload(email_address):
    """Build an SNS payload containing an SES complaint notification."""
    return _make_sns_payload(
        message_type="Notification",
        message_body={
            "notificationType": "Complaint",
            "complaint": {
                "complainedRecipients": [{"emailAddress": email_address}],
            },
        },
    )


class SESWebhookTest(TestCase):
    """Tests for the SES bounce/complaint webhook via SNS."""

    @patch("newsletter.views.verify_sns_signature", return_value=True)
    @patch("newsletter.views.requests.get")
    def test_handles_subscription_confirmation(self, mock_get, mock_verify):
        subscribe_url = "https://sns.us-east-1.amazonaws.com/confirm?token=abc"
        payload = _make_sns_payload(
            message_type="SubscriptionConfirmation",
            message_body="You have chosen to subscribe",
            sns_type="SubscriptionConfirmation",
        )
        payload["SubscribeURL"] = subscribe_url
        payload["Token"] = "abc123"

        response = self.client.post(
            "/newsletter/ses-webhook/",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_AMZ_SNS_MESSAGE_TYPE="SubscriptionConfirmation",
        )

        self.assertEqual(response.status_code, 200)
        mock_get.assert_called_once_with(subscribe_url, timeout=10)

    @patch("newsletter.views.verify_sns_signature", return_value=True)
    def test_processes_bounce_notification(self, mock_verify):
        subscriber = Subscriber.objects.create(
            email="bounce@example.com", status=Subscriber.STATUS_CONFIRMED
        )
        payload = _make_bounce_payload("bounce@example.com")

        response = self.client.post(
            "/newsletter/ses-webhook/",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_AMZ_SNS_MESSAGE_TYPE="Notification",
        )

        self.assertEqual(response.status_code, 200)
        subscriber.refresh_from_db()
        self.assertEqual(subscriber.status, Subscriber.STATUS_BOUNCED)
        self.assertIsNotNone(subscriber.bounced_at)
        log = SendLog.objects.get(subscriber=subscriber)
        self.assertEqual(log.event_type, SendLog.EVENT_BOUNCE)

    @patch("newsletter.views.verify_sns_signature", return_value=True)
    def test_processes_complaint_notification(self, mock_verify):
        subscriber = Subscriber.objects.create(
            email="complainer@example.com", status=Subscriber.STATUS_CONFIRMED
        )
        payload = _make_complaint_payload("complainer@example.com")

        response = self.client.post(
            "/newsletter/ses-webhook/",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_AMZ_SNS_MESSAGE_TYPE="Notification",
        )

        self.assertEqual(response.status_code, 200)
        subscriber.refresh_from_db()
        self.assertEqual(subscriber.status, Subscriber.STATUS_UNSUBSCRIBED)
        self.assertIsNotNone(subscriber.unsubscribed_at)
        log = SendLog.objects.get(subscriber=subscriber)
        self.assertEqual(log.event_type, SendLog.EVENT_COMPLAINT)

    @patch("newsletter.views.verify_sns_signature", return_value=False)
    def test_rejects_invalid_signature(self, mock_verify):
        subscriber = Subscriber.objects.create(
            email="test@example.com", status=Subscriber.STATUS_CONFIRMED
        )
        payload = _make_bounce_payload("test@example.com")

        response = self.client.post(
            "/newsletter/ses-webhook/",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_AMZ_SNS_MESSAGE_TYPE="Notification",
        )

        self.assertEqual(response.status_code, 403)
        subscriber.refresh_from_db()
        self.assertEqual(subscriber.status, Subscriber.STATUS_CONFIRMED)
        self.assertFalse(SendLog.objects.exists())

    @patch("newsletter.views.verify_sns_signature", return_value=True)
    def test_returns_200_for_unmatched_bounce_email(self, mock_verify):
        payload = _make_bounce_payload("unknown@example.com")

        response = self.client.post(
            "/newsletter/ses-webhook/",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_AMZ_SNS_MESSAGE_TYPE="Notification",
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(SendLog.objects.exists())


class SNSVerificationTest(SimpleTestCase):
    """Unit tests for SNS signature verification helpers."""

    def test_build_canonical_message_notification(self):
        from newsletter.sns import _build_canonical_message

        body = {
            "Type": "Notification",
            "MessageId": "msg-123",
            "TopicArn": "arn:aws:sns:us-east-1:123:topic",
            "Message": "Hello",
            "Timestamp": "2026-03-19T12:00:00.000Z",
            "Subject": "Test Subject",
        }
        result = _build_canonical_message(body)
        expected = (
            "Message\nHello\n"
            "MessageId\nmsg-123\n"
            "Subject\nTest Subject\n"
            "Timestamp\n2026-03-19T12:00:00.000Z\n"
            "TopicArn\narn:aws:sns:us-east-1:123:topic\n"
            "Type\nNotification\n"
        )
        self.assertEqual(result, expected)

    def test_build_canonical_message_notification_without_subject(self):
        from newsletter.sns import _build_canonical_message

        body = {
            "Type": "Notification",
            "MessageId": "msg-123",
            "TopicArn": "arn:aws:sns:us-east-1:123:topic",
            "Message": "Hello",
            "Timestamp": "2026-03-19T12:00:00.000Z",
        }
        result = _build_canonical_message(body)
        # Subject should be omitted entirely when not present
        self.assertNotIn("Subject", result)

    def test_build_canonical_message_subscription_confirmation(self):
        from newsletter.sns import _build_canonical_message

        body = {
            "Type": "SubscriptionConfirmation",
            "MessageId": "msg-456",
            "TopicArn": "arn:aws:sns:us-east-1:123:topic",
            "Message": "Confirm",
            "Timestamp": "2026-03-19T12:00:00.000Z",
            "SubscribeURL": "https://sns.us-east-1.amazonaws.com/confirm",
            "Token": "token-abc",
        }
        result = _build_canonical_message(body)
        expected = (
            "Message\nConfirm\n"
            "MessageId\nmsg-456\n"
            "SubscribeURL\nhttps://sns.us-east-1.amazonaws.com/confirm\n"
            "Timestamp\n2026-03-19T12:00:00.000Z\n"
            "Token\ntoken-abc\n"
            "TopicArn\narn:aws:sns:us-east-1:123:topic\n"
            "Type\nSubscriptionConfirmation\n"
        )
        self.assertEqual(result, expected)

    def test_validate_cert_url_rejects_non_https(self):
        from newsletter.sns import _validate_cert_url

        self.assertFalse(_validate_cert_url("http://sns.us-east-1.amazonaws.com/cert.pem"))

    def test_validate_cert_url_rejects_non_amazonaws(self):
        from newsletter.sns import _validate_cert_url

        self.assertFalse(_validate_cert_url("https://evil.example.com/cert.pem"))

    def test_validate_cert_url_rejects_non_pem(self):
        from newsletter.sns import _validate_cert_url

        self.assertFalse(_validate_cert_url("https://sns.us-east-1.amazonaws.com/cert.txt"))

    def test_validate_cert_url_accepts_valid(self):
        from newsletter.sns import _validate_cert_url

        self.assertTrue(_validate_cert_url("https://sns.us-east-1.amazonaws.com/cert.pem"))
        self.assertTrue(_validate_cert_url("https://sns.eu-west-1.amazonaws.com/path/to/cert.pem"))
