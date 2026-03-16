import uuid
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase, override_settings

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
