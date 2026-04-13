# Newsletter Operations Guide

## Emergency: Stop Sending Emails

**Fastest option — disable the cron job on Opalstack:**

```bash
crontab -e
# Comment out or delete the send_newsletter line:
# */15 * * * * cd /path/to/project && /path/to/python manage.py send_newsletter >> /path/to/logs/newsletter.log 2>&1
```

This stops new newsletters from being sent. Already-queued sends (mid-execution) will finish, but no new runs will start.

**Alternative — disable SES sending without touching cron:**

Set `NEWSLETTER_USE_SES=False` in the environment variables on Opalstack and restart the app. The cron will still run but emails will go through Django's default SMTP backend instead of SES. If you also want to prevent any email at all, set `DJANGO_EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend` (emails will be written to stdout/log instead of sent).

**Nuclear option — revoke SES credentials:**

In AWS Console: IAM > Users > `dtraleigh-newsletter-app` > Security credentials > deactivate or delete the access key. All SES sends will fail immediately. Re-create the key and update env vars to restore.

---

## Log Locations

### Opalstack — cron output

The cron job appends stdout/stderr to the log file specified in the crontab line:

```
>> /path/to/logs/newsletter.log 2>&1
```

This captures the management command's output: "Sending newsletter for: ...", "Sent to N subscribers", "No new posts found", etc.

### Django application logs

- **`debug.txt`** — project root, rotating file (50MB max). Contains log entries from the `django` logger (all apps except newsletter).
- **`newsletter-debug.txt`** — project root, rotating file (50MB max). Dedicated to the newsletter app. Contains all log entries from `newsletter.email`, `newsletter.views`, `newsletter.sns`, and `newsletter.management.commands.send_newsletter` at INFO level and above.

Both are configured in `myproject/settings.py` under the `LOGGING` setting.

### What gets logged where

| Event | Logger | Level | Destination |
|---|---|---|---|
| Confirmation email sent | `newsletter.email` | INFO | Root logger (console/nowhere by default) |
| Failed to send confirmation/newsletter | `newsletter.email` | ERROR | Root logger |
| SNS signature verification failed | `newsletter.views`, `newsletter.sns` | WARNING | Root logger |
| SNS subscription confirmed | `newsletter.views` | INFO | Root logger |
| Bounce/complaint for unknown email | `newsletter.views` | INFO | Root logger |
| Abandoned retry after 24h | `newsletter.management.commands.send_newsletter` | WARNING | Root logger |
| All management command output | stdout | — | Cron log file |

---

## Health Checks

### Subscriber stats (Django shell)

```bash
python manage.py shell -c "
from newsletter.models import Subscriber
for status in ['confirmed', 'unconfirmed', 'unsubscribed', 'bounced']:
    print(f'{status}: {Subscriber.objects.filter(status=status).count()}')
print(f'Total: {Subscriber.objects.count()}')
"
```

### Recent send activity

```bash
python manage.py shell -c "
from newsletter.models import SentPost, SendLog
# Last 5 newsletters sent
for sp in SentPost.objects.filter(seeded=False).order_by('-sent_at')[:5]:
    print(f'{sp.sent_at.strftime(\"%Y-%m-%d %H:%M\")} | {sp.title[:60]} | {sp.recipient_count} recipients')
print()
# Recent errors
errors = SendLog.objects.filter(event_type='error').order_by('-created_at')[:5]
if errors:
    for e in errors:
        print(f'{e.created_at.strftime(\"%Y-%m-%d %H:%M\")} | {e.detail[:80]}')
else:
    print('No recent errors.')
"
```

### Check for stuck sends (SentPost with recipient_count=0, not seeded)

```bash
python manage.py shell -c "
from newsletter.models import SentPost
stuck = SentPost.objects.filter(recipient_count=0, seeded=False)
if stuck.exists():
    for sp in stuck:
        print(f'STUCK: {sp.title} (guid={sp.guid}, sent_at={sp.sent_at})')
else:
    print('No stuck sends.')
"
```

These are posts where the send started but never completed. If they're less than 24 hours old, the next cron run will retry them. After 24 hours, they're abandoned with a warning log.

### Bounce and complaint activity

```bash
python manage.py shell -c "
from newsletter.models import SendLog
from django.utils import timezone
from datetime import timedelta
since = timezone.now() - timedelta(days=30)
bounces = SendLog.objects.filter(event_type='bounce', created_at__gte=since).count()
complaints = SendLog.objects.filter(event_type='complaint', created_at__gte=since).count()
print(f'Last 30 days: {bounces} bounces, {complaints} complaints')
"
```

High bounce rates (>5%) or any complaints are a warning sign for SES reputation. See "SES Sending Health" below.

---

## AWS Health Checks

### SES sending quota and reputation (CLI)

```bash
aws ses get-send-quota
```

Shows `Max24HourSend`, `SentLast24Hours`, and `MaxSendRate`. Make sure you're not approaching limits.

### SES account status

```bash
aws sesv2 get-account
```

Check `SendingEnabled` is `true` and `EnforcementStatus` is `HEALTHY`. If Amazon puts your account under review, `EnforcementStatus` changes to `PROBATION` or `SHUTDOWN`.

### SES bounce/complaint rates (Console)

**SES > Account dashboard > Reputation metrics** shows:
- Bounce rate (keep below 5%, ideally under 2%)
- Complaint rate (keep below 0.1%)

Amazon will put your account on probation if these thresholds are exceeded.

### SNS subscription health

```bash
aws sns list-subscriptions-by-topic --topic-arn "arn:aws:sns:us-east-1:649503295188:dtraleigh-ses-notifications"
```

The HTTPS subscription to `https://apps.dtraleigh.com/newsletter/ses-webhook/` should show `SubscriptionArn` (not "PendingConfirmation"). If it shows pending, the webhook isn't reachable or isn't confirming properly.

### Verify domain identity is still valid

```bash
aws ses get-identity-verification-attributes --identities dtraleigh.com
```

Should show `"VerificationStatus": "Success"`. If it shows "Pending" or "Failed", check your DNS DKIM records.

---

## Common Maintenance Tasks

### Manually trigger a newsletter send

```bash
cd /path/to/project && python manage.py send_newsletter
```

This is the same command the cron runs. It checks the RSS feed, compares against `SentPost` records, and sends any new posts. Safe to run anytime — idempotent.

### Re-seed after clearing SentPost records

If you ever need to clear `SentPost` records and re-mark the current feed as already-sent:

```bash
python manage.py send_newsletter --seed
```

**Important:** Only run `--seed` when there are no confirmed subscribers, or when the cron job is disabled. Seeded records are protected from being retried, but it's safest to seed while sending is paused.

### Remove a subscriber manually

```bash
python manage.py shell -c "
from newsletter.models import Subscriber
s = Subscriber.objects.get(email='someone@example.com')
print(f'Status: {s.status}')
s.status = 'unsubscribed'
s.save(update_fields=['status'])
print('Done.')
"
```

### View a subscriber's full history

```bash
python manage.py shell -c "
from newsletter.models import Subscriber, SendLog
s = Subscriber.objects.get(email='someone@example.com')
print(f'{s.email} | status={s.status} | created={s.created_at} | confirmed={s.confirmed_at}')
for log in SendLog.objects.filter(subscriber=s).order_by('-created_at')[:10]:
    print(f'  {log.created_at.strftime(\"%Y-%m-%d %H:%M\")} | {log.event_type} | {log.detail[:60]}')
"
```

### Export confirmed subscriber list

```bash
python manage.py shell -c "
from newsletter.models import Subscriber
for s in Subscriber.objects.filter(status='confirmed').order_by('email'):
    print(s.email)
"
```

### Check what the RSS feed currently has

```bash
python manage.py shell -c "
import feedparser
feed = feedparser.parse('https://dtraleigh.com/feed/')
for e in feed.entries:
    guid = e.get('id') or e.get('link')
    print(f'{e.get(\"title\", \"?\")} | {guid}')
"
```

### Test email sending without a real newsletter

Send a confirmation email to a test address to verify SES is working:

```bash
python manage.py shell -c "
from newsletter.models import Subscriber
from newsletter.email import send_confirmation_email
s, _ = Subscriber.objects.get_or_create(email='your-test@example.com')
send_confirmation_email(s)
print('Sent.')
"
```

---

## Django Admin

All newsletter models are registered in the Django admin at `https://apps.dtraleigh.com/admin/`:

- **Subscribers** — `/admin/newsletter/subscriber/` — search by email, filter by status
- **Sent Posts** — `/admin/newsletter/sentpost/` — shows title, sent_at, recipient_count
- **Send Logs** — `/admin/newsletter/sendlog/` — filter by event_type to see errors, bounces, complaints

The admin is the quickest way to check on things without writing shell commands.

---

## Troubleshooting

### "No new posts found" but there's a new blog post

1. Check that the post appears in the RSS feed: `https://dtraleigh.com/feed/`
2. Check if a `SentPost` record already exists for its GUID (it may have been seeded or already sent)
3. If the `SentPost` exists with `recipient_count=0` and `seeded=True`, it was intentionally marked as sent. Delete the record if you want to send it.

### Emails not arriving

1. Check the cron log for errors
2. Check `SendLog` for `error` event types
3. Verify SES is enabled: `aws ses get-send-quota` (check `SentLast24Hours` is incrementing)
4. Verify SES account is healthy: `aws sesv2 get-account`
5. Check spam folders — new sending domains often land in spam initially

### Bounce rate climbing

1. Check `SendLog` for recent bounces: which addresses are bouncing?
2. The webhook automatically marks bounced subscribers as `bounced` so they won't receive future sends
3. If the webhook isn't working (SNS subscription broken), bounced addresses will keep getting mail — check SNS subscription status
4. Review SES reputation metrics in the console

### SNS webhook not processing bounces/complaints

1. Verify the SNS subscription is confirmed (see "SNS subscription health" above)
2. Check Django logs for SNS signature verification failures
3. Verify the app is deployed and `https://apps.dtraleigh.com/newsletter/ses-webhook/` is reachable
4. Test with: `curl -s -X POST https://apps.dtraleigh.com/newsletter/ses-webhook/ -w "%{http_code}"` (expect 400, meaning the endpoint is up but no valid JSON was sent)
