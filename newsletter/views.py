import logging
import uuid

from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from .email import send_confirmation_email
from .forms import SubscribeForm
from .models import Subscriber

logger = logging.getLogger(__name__)


@ratelimit(key="ip", rate="5/h", method="POST", block=False)
def subscribe(request):
    if request.method == "POST":
        was_limited = getattr(request, "limited", False)
        if was_limited:
            return render(request, "newsletter/subscribe_success.html")

        form = SubscribeForm(request.POST)
        if form.is_valid():
            # Honeypot check — silently reject if filled
            if form.cleaned_data.get("website"):
                return render(request, "newsletter/subscribe_success.html")

            email = form.cleaned_data["email"]

            try:
                subscriber = Subscriber.objects.get(email=email)

                if subscriber.status == Subscriber.STATUS_CONFIRMED:
                    # Already confirmed — show same success message to avoid leaking status
                    return render(request, "newsletter/subscribe_success.html")

                elif subscriber.status == Subscriber.STATUS_BOUNCED:
                    # Bounced — don't re-subscribe, show a specific message
                    return render(request, "newsletter/subscribe_bounced.html")

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

            return render(request, "newsletter/subscribe_success.html")
    else:
        form = SubscribeForm()

    return render(request, "newsletter/subscribe.html", {"form": form})


def confirm(request, token):
    try:
        subscriber = Subscriber.objects.get(token=token)
    except Subscriber.DoesNotExist:
        return render(request, "newsletter/confirm_invalid.html")

    if subscriber.status == Subscriber.STATUS_UNCONFIRMED:
        subscriber.status = Subscriber.STATUS_CONFIRMED
        subscriber.confirmed_at = timezone.now()
        subscriber.save(update_fields=["status", "confirmed_at"])
        return render(request, "newsletter/confirm_success.html")

    if subscriber.status == Subscriber.STATUS_CONFIRMED:
        return render(request, "newsletter/confirm_already.html")

    # Any other status (unsubscribed, bounced) — token is no longer valid
    return render(request, "newsletter/confirm_invalid.html")


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
        return render(request, "newsletter/confirm_invalid.html")

    if request.method == "POST":
        subscriber.status = Subscriber.STATUS_UNSUBSCRIBED
        subscriber.unsubscribed_at = timezone.now()
        subscriber.save(update_fields=["status", "unsubscribed_at"])
        return render(request, "newsletter/unsubscribe_success.html")

    return render(request, "newsletter/unsubscribe_confirm.html", {
        "subscriber": subscriber,
    })


@csrf_exempt
@require_POST
def ses_webhook(request):
    """Placeholder for Phase 5: SES bounce/complaint webhook via SNS."""
    return HttpResponse(status=200)
