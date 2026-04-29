import json
import logging
import uuid

import requests
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from .email import send_confirmation_email
from .forms import SubscribeForm
from .models import SendLog, Subscriber
from .sns import verify_sns_signature

logger = logging.getLogger(__name__)


TITLE_PREFIX = "The Raleigh Connoisseur"


@ratelimit(key="ip", rate="5/h", method="POST", block=False)
def subscribe(request):
    if request.method == "POST":
        was_limited = getattr(request, "limited", False)
        if was_limited:
            return render(request, "newsletter/subscribe_success.html",
                          {"page_title": f"{TITLE_PREFIX} - Subscription Pending"})

        form = SubscribeForm(request.POST)
        if form.is_valid():
            # Honeypot check — silently reject if filled
            if form.cleaned_data.get("website"):
                return render(request, "newsletter/subscribe_success.html",
                              {"page_title": f"{TITLE_PREFIX} - Subscription Pending"})

            email = form.cleaned_data["email"]

            try:
                subscriber = Subscriber.objects.get(email=email)

                if subscriber.status == Subscriber.STATUS_CONFIRMED:
                    # Already confirmed — show same success message to avoid leaking status
                    return render(request, "newsletter/subscribe_success.html",
                                  {"page_title": f"{TITLE_PREFIX} - Subscription Pending"})

                elif subscriber.status == Subscriber.STATUS_BOUNCED:
                    # Bounced — don't re-subscribe, show a specific message
                    return render(request, "newsletter/subscribe_bounced.html",
                                  {"page_title": f"{TITLE_PREFIX} - Subscription Issue"})

                elif subscriber.status == Subscriber.STATUS_UNCONFIRMED:
                    # Resend confirmation with a fresh token
                    subscriber.token = uuid.uuid4()
                    subscriber.save(update_fields=["token"])
                    send_confirmation_email(subscriber)

                elif subscriber.status == Subscriber.STATUS_UNSUBSCRIBED:
                    # Reset to unconfirmed and send fresh confirmation
                    subscriber.status = Subscriber.STATUS_UNCONFIRMED
                    subscriber.token = uuid.uuid4()
                    subscriber.unsubscribed_at = None
                    subscriber.save(update_fields=["status", "token", "unsubscribed_at"])
                    send_confirmation_email(subscriber)

            except Subscriber.DoesNotExist:
                subscriber = Subscriber.objects.create(email=email)
                send_confirmation_email(subscriber)

            return render(request, "newsletter/subscribe_success.html",
                          {"page_title": f"{TITLE_PREFIX} - Subscription Pending"})
    else:
        form = SubscribeForm()

    return render(request, "newsletter/subscribe.html", {
        "form": form,
        "page_title": f"{TITLE_PREFIX} - Subscribe",
    })


def confirm(request, token):
    try:
        subscriber = Subscriber.objects.get(token=token)
    except Subscriber.DoesNotExist:
        return render(request, "newsletter/confirm_invalid.html",
                      {"page_title": f"{TITLE_PREFIX} - Invalid Link"})

    if subscriber.status == Subscriber.STATUS_UNCONFIRMED:
        subscriber.status = Subscriber.STATUS_CONFIRMED
        subscriber.confirmed_at = timezone.now()
        subscriber.save(update_fields=["status", "confirmed_at"])
        return render(request, "newsletter/confirm_success.html",
                      {"page_title": f"{TITLE_PREFIX} - Subscription Confirmed"})

    if subscriber.status == Subscriber.STATUS_CONFIRMED:
        return render(request, "newsletter/confirm_already.html",
                      {"page_title": f"{TITLE_PREFIX} - Already Subscribed"})

    # Any other status (unsubscribed, bounced) — token is no longer valid
    return render(request, "newsletter/confirm_invalid.html",
                  {"page_title": f"{TITLE_PREFIX} - Invalid Link"})


@csrf_exempt
def unsubscribe(request, token):
    """Unsubscribe view.

    CSRF is exempt because email clients send one-click unsubscribe POSTs
    (List-Unsubscribe-Post header) without a CSRF token. The UUID token
    in the URL serves as the authentication mechanism.
    """
    try:
        subscriber = Subscriber.objects.get(token=token)
    except Subscriber.DoesNotExist:
        return render(request, "newsletter/confirm_invalid.html",
                      {"page_title": f"{TITLE_PREFIX} - Invalid Link"})

    if request.method == "POST":
        subscriber.status = Subscriber.STATUS_UNSUBSCRIBED
        subscriber.unsubscribed_at = timezone.now()
        subscriber.save(update_fields=["status", "unsubscribed_at"])
        return render(request, "newsletter/unsubscribe_success.html",
                      {"page_title": f"{TITLE_PREFIX} - Unsubscribed"})

    return render(request, "newsletter/unsubscribe_confirm.html", {
        "subscriber": subscriber,
        "page_title": f"{TITLE_PREFIX} - Unsubscribe",
    })


@csrf_exempt
@require_POST
def ses_webhook(request):
    """Handle SES bounce/complaint notifications delivered via SNS."""
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return HttpResponse(status=400)

    if not verify_sns_signature(payload):
        logger.warning("SNS signature verification failed for ses-webhook request")
        return HttpResponse(status=403)

    message_type = request.headers.get("x-amz-sns-message-type", "")

    if message_type == "SubscriptionConfirmation":
        subscribe_url = payload.get("SubscribeURL")
        if subscribe_url:
            try:
                requests.get(subscribe_url, timeout=10)
                logger.info("Confirmed SNS subscription: %s", payload.get("TopicArn"))
            except Exception:
                logger.error("Failed to confirm SNS subscription", exc_info=True)
        return HttpResponse(status=200)

    if message_type == "Notification":
        try:
            message = json.loads(payload.get("Message", "{}"))
        except (json.JSONDecodeError, ValueError):
            logger.warning("Failed to parse SNS notification Message")
            return HttpResponse(status=200)

        notification_type = message.get("notificationType")
        if notification_type == "Bounce":
            _process_bounce(message)
        elif notification_type == "Complaint":
            _process_complaint(message)

    return HttpResponse(status=200)


def _process_bounce(message):
    """Mark bounced subscribers and log the event."""
    recipients = message.get("bounce", {}).get("bouncedRecipients", [])
    for recipient in recipients:
        email_addr = recipient.get("emailAddress", "").lower()
        try:
            subscriber = Subscriber.objects.get(email__iexact=email_addr)
            subscriber.status = Subscriber.STATUS_BOUNCED
            subscriber.bounced_at = timezone.now()
            subscriber.save(update_fields=["status", "bounced_at"])
            SendLog.objects.create(
                subscriber=subscriber,
                event_type=SendLog.EVENT_BOUNCE,
                detail=f"Bounce for {email_addr}",
            )
        except Subscriber.DoesNotExist:
            logger.info("Bounce for unknown email: %s", email_addr)


def _process_complaint(message):
    """Mark complained subscribers as unsubscribed and log the event."""
    recipients = message.get("complaint", {}).get("complainedRecipients", [])
    for recipient in recipients:
        email_addr = recipient.get("emailAddress", "").lower()
        try:
            subscriber = Subscriber.objects.get(email__iexact=email_addr)
            subscriber.status = Subscriber.STATUS_UNSUBSCRIBED
            subscriber.unsubscribed_at = timezone.now()
            subscriber.save(update_fields=["status", "unsubscribed_at"])
            SendLog.objects.create(
                subscriber=subscriber,
                event_type=SendLog.EVENT_COMPLAINT,
                detail=f"Complaint for {email_addr}",
            )
        except Subscriber.DoesNotExist:
            logger.info("Complaint for unknown email: %s", email_addr)
