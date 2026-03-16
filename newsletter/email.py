import logging
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, send_mail
from django.template.loader import render_to_string

from .models import SendLog, Subscriber

logger = logging.getLogger(__name__)


def _get_ses_client():
    """Return a boto3 SES client, validating credentials are configured."""
    if not settings.AWS_SES_ACCESS_KEY_ID or not settings.AWS_SES_SECRET_ACCESS_KEY:
        raise ValueError(
            "NEWSLETTER_USE_SES is True but AWS_SES_ACCESS_KEY_ID and/or "
            "AWS_SES_SECRET_ACCESS_KEY are not set."
        )
    import boto3

    return boto3.client(
        "ses",
        region_name=settings.AWS_SES_REGION,
        aws_access_key_id=settings.AWS_SES_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SES_SECRET_ACCESS_KEY,
    )


def _send_raw_ses_email(from_email, to_email, subject, html_body, text_body, unsubscribe_url):
    """Send an email via SES send_raw_email with List-Unsubscribe headers."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email
    msg["List-Unsubscribe"] = f"<{unsubscribe_url}>"
    msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"

    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    client = _get_ses_client()
    client.send_raw_email(
        Source=from_email,
        Destinations=[to_email],
        RawMessage={"Data": msg.as_string()},
    )


def _send_django_email(from_email, to_email, subject, html_body, text_body, unsubscribe_url):
    """Send an email via Django's EmailMultiAlternatives with List-Unsubscribe headers."""
    headers = {
        "List-Unsubscribe": f"<{unsubscribe_url}>",
        "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
    }
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=from_email,
        to=[to_email],
        headers=headers,
    )
    email.attach_alternative(html_body, "text/html")
    email.send(fail_silently=False)


def send_confirmation_email(subscriber):
    """Send a double opt-in confirmation email to the subscriber.

    Uses Django's built-in email backend when NEWSLETTER_USE_SES is False,
    or boto3 SES when NEWSLETTER_USE_SES is True.
    """
    base_url = settings.NEWSLETTER_BASE_URL.rstrip("/")
    confirm_url = f"{base_url}/newsletter/confirm/{subscriber.token}/"

    subject = "Confirm your subscription to DTRaleigh"
    text_body = (
        "You've requested to subscribe to the DTRaleigh newsletter.\n\n"
        f"Please confirm your subscription by visiting this link:\n{confirm_url}\n\n"
        "If you didn't request this, you can safely ignore this email."
    )
    html_body = (
        "<html><body>"
        "<p>You've requested to subscribe to the DTRaleigh newsletter.</p>"
        f'<p><a href="{confirm_url}" style="display:inline-block;padding:10px 20px;'
        'background-color:#007bff;color:#ffffff;text-decoration:none;border-radius:4px;">'
        "Confirm your subscription</a></p>"
        f'<p>Or copy and paste this link into your browser:<br>{confirm_url}</p>'
        "<p>If you didn't request this, you can safely ignore this email.</p>"
        "</body></html>"
    )

    from_email = settings.NEWSLETTER_FROM_EMAIL

    try:
        if settings.NEWSLETTER_USE_SES:
            client = _get_ses_client()
            client.send_email(
                Source=from_email,
                Destination={"ToAddresses": [subscriber.email]},
                Message={
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": {
                        "Text": {"Data": text_body, "Charset": "UTF-8"},
                        "Html": {"Data": html_body, "Charset": "UTF-8"},
                    },
                },
            )
        else:
            send_mail(
                subject=subject,
                message=text_body,
                from_email=from_email,
                recipient_list=[subscriber.email],
                html_message=html_body,
                fail_silently=False,
            )

        SendLog.objects.create(
            subscriber=subscriber,
            event_type=SendLog.EVENT_CONFIRMATION_SENT,
            detail=f"Confirmation email sent to {subscriber.email}",
        )
        logger.info("Confirmation email sent to %s", subscriber.email)
    except Exception as e:
        SendLog.objects.create(
            subscriber=subscriber,
            event_type=SendLog.EVENT_ERROR,
            detail=f"Failed to send confirmation email: {e}",
        )
        logger.error("Failed to send confirmation email to %s: %s", subscriber.email, e)
        raise


def send_newsletter(subject, html_content, text_content, post_url, sent_post):
    """Send a newsletter email to all confirmed subscribers.

    Args:
        subject: Email subject line.
        html_content: The blog post HTML content (inner body, not full email).
        text_content: The blog post plain text content.
        post_url: URL to the original blog post ("Read on the web" link).
        sent_post: SentPost instance to link SendLog entries to.

    Returns:
        Number of successfully sent emails.
    """
    from_email = settings.NEWSLETTER_FROM_EMAIL
    base_url = settings.NEWSLETTER_BASE_URL.rstrip("/")
    mailing_address = settings.NEWSLETTER_MAILING_ADDRESS
    subscribers = Subscriber.objects.filter(status=Subscriber.STATUS_CONFIRMED)
    success_count = 0

    for subscriber in subscribers:
        unsubscribe_url = f"{base_url}/newsletter/unsubscribe/{subscriber.token}/"

        template_context = {
            "html_content": html_content,
            "text_content": text_content,
            "post_url": post_url,
            "unsubscribe_url": unsubscribe_url,
            "mailing_address": mailing_address,
        }
        rendered_html = render_to_string(
            "newsletter/email/newsletter.html", template_context
        )
        rendered_text = render_to_string(
            "newsletter/email/newsletter.txt", template_context
        )

        try:
            if settings.NEWSLETTER_USE_SES:
                _send_raw_ses_email(
                    from_email, subscriber.email, subject,
                    rendered_html, rendered_text, unsubscribe_url,
                )
            else:
                _send_django_email(
                    from_email, subscriber.email, subject,
                    rendered_html, rendered_text, unsubscribe_url,
                )

            SendLog.objects.create(
                sent_post=sent_post,
                subscriber=subscriber,
                event_type=SendLog.EVENT_NEWSLETTER_SENT,
                detail=f"Newsletter sent to {subscriber.email}",
            )
            success_count += 1
        except Exception as e:
            SendLog.objects.create(
                sent_post=sent_post,
                subscriber=subscriber,
                event_type=SendLog.EVENT_ERROR,
                detail=f"Failed to send newsletter: {e}",
            )
            logger.error("Failed to send newsletter to %s: %s", subscriber.email, e)

        # Pace sends to stay under SES rate limit (14/sec default)
        if settings.NEWSLETTER_USE_SES:
            time.sleep(0.1)

    return success_count
