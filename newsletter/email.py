import logging

from django.conf import settings
from django.core.mail import send_mail

from .models import SendLog, Subscriber

logger = logging.getLogger(__name__)


def send_confirmation_email(subscriber):
    """Send a double opt-in confirmation email to the subscriber.

    Uses Django's built-in email backend when NEWSLETTER_USE_SES is False.
    Phase 3 will add the SES path.
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
            # Phase 3: SES integration will go here
            raise NotImplementedError("SES sending not yet implemented")
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
