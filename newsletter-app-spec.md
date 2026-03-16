# Newsletter App Specification

## Overview

A new Django app called `newsletter` (already created) to be added to the existing Django project hosted at `apps.dtraleigh.com`. The app manages email newsletter subscriptions for the WordPress blog at `dtraleigh.com`, using Amazon SES for email delivery.

### Key Decisions (Already Made)

- **Email delivery**: Amazon SES (not self-hosted SMTP)
- **Signup flow**: Double opt-in (confirmation email required)
- **URL structure**: All web endpoints live under `apps.dtraleigh.com/newsletter/`
- **RSS source**: `https://dtraleigh.com/feed/` (standard WordPress RSS feed)
- **Sending identity**: `newsletter@dtraleigh.com` (or a subdomain like `mail.dtraleigh.com` — TBD by site owner)
- **Framework**: Django app within the existing project
- **Email sending library**: `boto3` (AWS SDK for Python)
- **Rate limiting**: `django-ratelimit` package
- **RSS parsing library**: `feedparser`
- **Email backend toggle**: `NEWSLETTER_USE_SES` setting — when `False`, uses Django's built-in email backend (useful for local testing); when `True`, uses boto3/SES for production

### Expected Scale

- ~1,000 subscribers
- ~1 blog post per week
- ~4,000–5,000 emails/month (newsletters + confirmations)

---

## Phase 1: Models and Admin

### Models

#### Subscriber

| Field | Type | Notes |
|-------|------|-------|
| `email` | EmailField | unique, indexed |
| `token` | UUIDField | default=uuid4, unique — used in confirmation and unsubscribe URLs |
| `status` | CharField | choices: `unconfirmed`, `confirmed`, `unsubscribed`, `bounced` |
| `created_at` | DateTimeField | auto_now_add |
| `confirmed_at` | DateTimeField | null=True, blank=True |
| `unsubscribed_at` | DateTimeField | null=True, blank=True |
| `bounced_at` | DateTimeField | null=True, blank=True |

#### SentPost

Tracks which RSS entries have already been mailed to prevent duplicate sends.

| Field | Type | Notes |
|-------|------|-------|
| `guid` | CharField | max_length=500, unique — the RSS entry's GUID or link |
| `title` | CharField | max_length=500 |
| `sent_at` | DateTimeField | auto_now_add |
| `recipient_count` | IntegerField | how many confirmed subscribers received it |

#### SendLog

| Field | Type | Notes |
|-------|------|-------|
| `sent_post` | ForeignKey | to SentPost, null=True |
| `subscriber` | ForeignKey | to Subscriber, null=True — links log entries to a specific subscriber |
| `event_type` | CharField | choices: `newsletter_sent`, `confirmation_sent`, `bounce`, `complaint`, `error` |
| `detail` | TextField | blank=True — error messages, bounce diagnostics, etc. |
| `created_at` | DateTimeField | auto_now_add |

### Admin Registration

Register all models with Django admin. For Subscriber, customize the list display to show email, status, created_at, and confirmed_at. Add list filters for status. Add search on email. For SentPost, show title, sent_at, and recipient_count.

---

## Phase 2: Subscribe, Confirm, and Unsubscribe Views

### URL Configuration

All URLs under `newsletter/`:

| URL Pattern | View | Method(s) |
|-------------|------|-----------|
| `subscribe/` | subscribe view | GET (form), POST (submit) |
| `confirm/<uuid:token>/` | confirm view | GET |
| `unsubscribe/<uuid:token>/` | unsubscribe view | GET, POST |
| `ses-webhook/` | SES bounce/complaint webhook | POST |

### Subscribe View

- GET: Render a simple form with an email field and a honeypot hidden field (e.g., a text input named `website` that should remain empty — bots tend to fill it in).
- POST: Validate the email. If the honeypot is filled, silently reject. If valid:
  - If a subscriber with this email already exists and is `confirmed`, show the same generic success message (to avoid leaking subscriber status).
  - If a subscriber exists and is `unconfirmed`, resend the confirmation email and reset the token.
  - If a subscriber exists and is `unsubscribed`, reset status to `unconfirmed`, generate a new token, clear `unsubscribed_at`, and send a fresh confirmation.
  - If a subscriber exists and is `bounced`, show a message that the email address is unable to receive the newsletter and suggest contacting support. This prevents repeated bounces from damaging SES sender reputation.
  - Otherwise, create a new `Subscriber` with status `unconfirmed` and send the confirmation email.
- Apply rate limiting using `django-ratelimit`: no more than 5 signup attempts per IP per hour. Rate-limited requests see the same success page (no indication of throttling).
- Show a success message: "Check your email for a confirmation link." — same message regardless of whether the email was already in the system (to avoid leaking subscriber status).

### Confirm View

- Accepts the UUID token via URL.
- Looks up the subscriber. If found and status is `unconfirmed`, set status to `confirmed`, set `confirmed_at`, and render a thank-you page.
- If the token is invalid or already confirmed, show an appropriate message (not an error — just "already confirmed" or "link expired").

### Unsubscribe View

- GET: Look up subscriber by token. Show a simple page confirming they want to unsubscribe, with a button/form to confirm.
- POST: Set status to `unsubscribed`, set `unsubscribed_at`, render a confirmation message.
- This must also support one-click unsubscribe via POST with no body, to satisfy the `List-Unsubscribe-Post` header requirement. If the POST has no form data but has a valid token, proceed with the unsubscribe.
- The entire unsubscribe view is CSRF-exempt (`@csrf_exempt`) because email clients send one-click unsubscribe POSTs without a CSRF token. The UUID token in the URL serves as the authentication mechanism.

### Templates

Keep templates simple and functional. They should inherit from a base template if the existing project has one, or use a minimal standalone base. Pages needed:

- `newsletter/subscribe.html` — the signup form
- `newsletter/subscribe_success.html` — "check your email" message
- `newsletter/subscribe_bounced.html` — message for bounced emails suggesting they contact support
- `newsletter/confirm_success.html` — "you're subscribed" message
- `newsletter/confirm_already.html` — "already confirmed" message (distinct from invalid token)
- `newsletter/confirm_invalid.html` — invalid/expired token
- `newsletter/unsubscribe_confirm.html` — "are you sure?" with button
- `newsletter/unsubscribe_success.html` — "you've been unsubscribed"

All templates extend `generic_base.html` (the project's existing Bootstrap 4 base template).

---

## Phase 3: SES Integration for Confirmation Emails

### Dependencies

Add to requirements:

```
boto3
feedparser
django-ratelimit  (already added in Phase 2)
```

### Django Settings

Add these settings via `django-environ` (the project's existing env-var library — do NOT hardcode credentials). Note: `NEWSLETTER_USE_SES`, `NEWSLETTER_FROM_EMAIL`, `NEWSLETTER_BASE_URL`, and `NEWSLETTER_SEND_ALL_NEW` were already added in Phase 2.

```python
# Newsletter configuration (added in Phase 2)
NEWSLETTER_USE_SES = env.bool("NEWSLETTER_USE_SES", default=False)
NEWSLETTER_FROM_EMAIL = env("NEWSLETTER_FROM_EMAIL", default="newsletter@dtraleigh.com")
NEWSLETTER_BASE_URL = env("NEWSLETTER_BASE_URL", default="https://apps.dtraleigh.com")
NEWSLETTER_SEND_ALL_NEW = env.bool("NEWSLETTER_SEND_ALL_NEW", default=True)
NEWSLETTER_MAILING_ADDRESS = env("NEWSLETTER_MAILING_ADDRESS", default="DTRaleigh, Raleigh, NC [UPDATE BEFORE GO-LIVE]")

# AWS SES Configuration (add in Phase 3)
AWS_SES_ACCESS_KEY_ID = env("AWS_SES_ACCESS_KEY_ID")
AWS_SES_SECRET_ACCESS_KEY = env("AWS_SES_SECRET_ACCESS_KEY")
AWS_SES_REGION = env("AWS_SES_REGION", default="us-east-1")
```

### SES Email Helper

The utility module `newsletter/email.py` was created in Phase 2 with Django's built-in email backend. Phase 3 adds the SES code path, gated by the `NEWSLETTER_USE_SES` setting. Functions:

#### `send_confirmation_email(subscriber)`

- Sends an email to the subscriber with a link to `{NEWSLETTER_BASE_URL}/newsletter/confirm/{subscriber.token}/`
- Subject: Something like "Confirm your subscription to DTRaleigh"
- Body: Simple HTML with the confirmation link and a plain text alternative
- When `NEWSLETTER_USE_SES` is `True`, uses `boto3` SES client's `send_email` or `send_raw_email`; when `False`, uses Django's built-in `send_mail` (for local testing)
- Log the send in SendLog

#### `send_newsletter(subject, html_content, text_content, post_url, sent_post)`

- Queries all `confirmed` subscribers
- For each subscriber, sends an email via SES with:
  - The newsletter content
  - A `List-Unsubscribe` header: `<https://apps.dtraleigh.com/newsletter/unsubscribe/{token}/>`
  - A `List-Unsubscribe-Post` header: `List-Unsubscribe=One-Click`
  - Both HTML and plain text MIME parts
- Use `send_raw_email` to set custom headers (the simpler `send_email` API doesn't support `List-Unsubscribe`)
- Send with pacing of ~10/sec (`time.sleep(0.1)`) to stay comfortably under SES's 14/sec default rate limit
- Log each send/error in SendLog, linked to the `sent_post` parameter
- Return count of successful sends
- When `NEWSLETTER_USE_SES` is `False`, uses Django's `EmailMultiAlternatives` with the same custom headers (feature-parity fallback for testing)

### Email Templates

#### Confirmation Email

Simple and professional. Include:

- A brief message: "You've requested to subscribe to the DTRaleigh newsletter."
- The confirmation link (prominently displayed)
- A note: "If you didn't request this, you can safely ignore this email."

#### Newsletter Email

Implemented as Django templates rendered per-subscriber by `send_newsletter()`:

- **`newsletter/templates/newsletter/email/newsletter.html`** — Table-based single-column layout (600px max width), all CSS inline. Includes `{{ html_content|safe }}` slot for blog post content, "Read on the web" button linking to `{{ post_url }}`, and footer with unsubscribe link, `NEWSLETTER_MAILING_ADDRESS`, and "you subscribed" note.
- **`newsletter/templates/newsletter/email/newsletter.txt`** — Plain text equivalent with the same template variables.

The `send_newsletter()` function renders these templates per subscriber, injecting their personalized unsubscribe URL. The email subject uses the post title directly (Phase 4 management command provides it).

---

## Phase 4: RSS Poller and Newsletter Send

### Management Command: `send_newsletter`

Create `newsletter/management/commands/send_newsletter.py`:

1. Fetch the RSS feed from `https://dtraleigh.com/feed/` using `feedparser`.
2. For each entry in the feed, check if its GUID (or link, as fallback) exists in the `SentPost` table.
3. For any new entry:
   a. Extract the title, link, and content (prefer `content:encoded` for full HTML, fall back to `summary`/`description`).
   b. Render the newsletter email template with this content.
   c. Call `send_newsletter()` to send to all confirmed subscribers.
   d. Create a `SentPost` record with the GUID, title, and recipient count.
4. Handle multiple new posts: if the feed has more than one unsent entry, send them in chronological order (oldest first). Controlled by the `NEWSLETTER_SEND_ALL_NEW` Django setting (default `True`): when `True`, sends all unsent posts; when `False`, sends only the most recent unsent post.

### Cron Configuration

This command should be run via cron on Opalstack. Suggested schedule: every 15–30 minutes.

```
*/15 * * * * cd /path/to/django/project && /path/to/python manage.py send_newsletter >> /path/to/logs/newsletter.log 2>&1
```

The site owner will configure the actual cron job and paths on Opalstack.

### Idempotency

The command must be safe to run repeatedly. The `SentPost` table is the guard against duplicate sends. Use database-level uniqueness on the GUID field. If the command crashes mid-send (after some subscribers received the email but before the `SentPost` is created), the next run will re-send to everyone. To mitigate this:

- Create the `SentPost` record *before* starting the send (with `recipient_count=0`)
- Update `recipient_count` after all sends complete
- If the record exists but `recipient_count` is 0, that indicates a failed previous attempt — the command should either skip it or retry, based on a flag

---

## Phase 5: Bounce and Complaint Webhook

### SES → SNS → Webhook Flow

SES publishes bounce and complaint notifications to an SNS topic. The SNS topic is configured to POST to `https://apps.dtraleigh.com/newsletter/ses-webhook/`.

### Webhook View

- Exempt from CSRF (use `@csrf_exempt` decorator)
- Handle three types of SNS messages:
  1. **SubscriptionConfirmation**: When first setting up, SNS sends a confirmation. The view should fetch the `SubscribeURL` from the payload to confirm the subscription. This can be done automatically with a GET request to that URL.
  2. **Notification** with bounce: Parse the bounced email address(es) from the SES bounce notification JSON. Set matching subscriber(s) to `bounced` status. Log in SendLog.
  3. **Notification** with complaint: Parse the complained email address(es). Set matching subscriber(s) to `unsubscribed` status. Log in SendLog.
- Verify the SNS message signature to prevent spoofed requests. The `boto3` library doesn't do this directly — you'll need to verify the signing certificate URL is from `sns.amazonaws.com`, fetch the cert, and validate the signature. Alternatively, use the `python-certvalidator` package or implement manual verification.
- Return 200 OK for all handled messages.

---

## AWS Setup Checklist (Manual Steps for Site Owner)

These steps are done in the AWS Console or CLI, not by the Django app:

1. **Verify domain in SES**: Add your sending domain and configure the three DKIM CNAME records in your DNS.
2. **Request SES production access**: Move out of sandbox mode. Describe use case as "double opt-in blog newsletter."
3. **Create IAM user**: Create a user with programmatic access. Attach a policy scoped to:
   - `ses:SendEmail`
   - `ses:SendRawEmail`
   - Save the access key and secret for Django settings.
4. **Create SNS topic**: Name it something like `dtraleigh-ses-notifications`.
5. **Configure SES notifications**: In SES, set bounce and complaint notifications to publish to the SNS topic.
6. **Create SNS subscription**: Add an HTTPS subscription pointing to `https://apps.dtraleigh.com/newsletter/ses-webhook/`. Deploy the webhook view first so it can handle the confirmation request.
7. **DNS records**: Add SPF, DKIM (from SES), and DMARC records to your domain's DNS.
8. **Configure environment variables** on Opalstack for the Django app:
   - `NEWSLETTER_USE_SES=True` (must be set to `True` for production SES sending)
   - `AWS_SES_ACCESS_KEY_ID`
   - `AWS_SES_SECRET_ACCESS_KEY`
   - `AWS_SES_REGION`
   - `NEWSLETTER_FROM_EMAIL`
   - `NEWSLETTER_BASE_URL`
   - `NEWSLETTER_SEND_ALL_NEW` (optional, defaults to `True`)
   - `NEWSLETTER_MAILING_ADDRESS` (CAN-SPAM physical address for email footer)
9. **Set up the cron job** on Opalstack for the `send_newsletter` management command.

---

## Build Order

Execute these phases in order. Each phase is independently testable.

1. **Phase 1**: Models and admin — verify you can create and manage subscribers in the admin.
2. **Phase 2**: Views, templates, forms, email helper, and URL configuration. Includes `django-ratelimit` for subscribe throttling, `NEWSLETTER_USE_SES` toggle (defaults to `False` to use Django's built-in email for testing), bounced-subscriber handling, and a placeholder `ses-webhook/` endpoint. Verify the signup form works, confirmation links work, unsubscribe links work.
3. **Phase 3**: SES integration — adds boto3/SES send path gated by `NEWSLETTER_USE_SES`, `send_newsletter()` function with per-subscriber personalization (unsubscribe links via Django email templates), `NEWSLETTER_MAILING_ADDRESS` setting, and Django `EmailMultiAlternatives` fallback for testing. Test with a real email address in SES sandbox mode (you can verify individual addresses in sandbox).
4. **Phase 4**: RSS poller — test with `manage.py send_newsletter` manually. Verify it detects new posts and sends.
5. **Phase 5**: Bounce webhook — deploy and test by sending to a known-bad address.

---

## Go Live Checklist

Before enabling the newsletter for real subscribers, ensure all of these are complete:

- [ ] **Set `NEWSLETTER_MAILING_ADDRESS`** — CAN-SPAM requires a valid physical postal address in every marketing email. A PO Box is acceptable. Update the env var to replace the placeholder.
- [ ] **Set `NEWSLETTER_USE_SES=True`** — Switch from Django's built-in email to SES for production sending.
- [ ] **Set `NEWSLETTER_FROM_EMAIL`** — Confirm the sending address (must be verified in SES).
- [ ] **Complete AWS Setup Checklist** (see section above) — domain verification, DKIM, SES production access, IAM user, SNS topic, webhook subscription.
- [ ] **Set up the cron job** for `manage.py send_newsletter` on Opalstack.
- [ ] **Test end-to-end** in SES sandbox mode — subscribe, confirm, receive a newsletter, unsubscribe, verify bounce webhook.
- [ ] **Request SES production access** — Move out of sandbox to send to unverified addresses.

---

## Test Strategy

Tests live in `newsletter/tests.py` and follow the project's existing patterns. Run with `python manage.py test newsletter`.

### Phases 1–3 (implemented)

All email sending is mocked (`@patch`) so no real emails are sent. Rate limiting is disabled in tests via `RATELIMIT_ENABLE=False`.

- **`SubscribeFormTest(SimpleTestCase)`** — Form validation: valid/invalid/empty email, honeypot field not required. No DB needed.
- **`SubscribeViewTest(TestCase)`** — Full subscribe flow: GET renders form, POST creates subscriber and sends confirmation, honeypot silently rejects, invalid email re-renders form, already-confirmed shows success (no status leak), unconfirmed resets token and resends, unsubscribed resets to unconfirmed, bounced shows bounced template.
- **`ConfirmViewTest(TestCase)`** — Token confirmation: unconfirmed → confirmed with timestamp, already confirmed shows "already" page, unsubscribed/bounced/invalid tokens show invalid page.
- **`UnsubscribeViewTest(TestCase)`** — Unsubscribe flow: GET shows confirmation with email, POST sets unsubscribed with timestamp, one-click POST (no form data) works, invalid token shows invalid page.
- **`SendConfirmationEmailTest(TestCase)`** — Email helper: Django backend calls `send_mail` and creates `confirmation_sent` SendLog, failure creates `error` SendLog and re-raises, confirmation URL contains subscriber token.
- **`SendNewsletterTest(TestCase)`** — Newsletter sending: sends only to confirmed subscribers, creates per-subscriber SendLog, partial failure logs error and continues, rendered email contains unsubscribe URL/post URL/mailing address.

### Phase 4 (with implementation)

- **`SendNewsletterCommandTest(TestCase)`** — Management command: parses RSS feed, creates SentPost for new entries, skips already-sent GUIDs (idempotency), sends in chronological order, respects `NEWSLETTER_SEND_ALL_NEW` setting.

### Phase 5 (with implementation)

- **`SESWebhookTest(TestCase)`** — SNS webhook: handles SubscriptionConfirmation, processes bounce notifications (sets subscriber to bounced, creates SendLog), processes complaint notifications (sets subscriber to unsubscribed), rejects messages with invalid signatures, returns 200 for all handled messages.

---

## Notes

- The site owner's existing Django project structure should be respected. Examine the project layout before creating files.
- Use the project's existing database backend (likely PostgreSQL on Opalstack, but confirm).
- Follow the project's existing patterns for settings, URL includes, and template structure.
- The CAN-SPAM physical mailing address is configured via `NEWSLETTER_MAILING_ADDRESS` setting — must be updated before go-live (see Go Live Checklist).
- For HTML email templates, start simple. A plain single-column table layout with inline CSS is sufficient. Fancy design can come later.
