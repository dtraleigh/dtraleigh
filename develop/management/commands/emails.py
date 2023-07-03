import logging
from datetime import datetime
from datetime import timedelta

from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from develop.models import *

logger = logging.getLogger("django")


def email_admins():
    admins = Subscriber.objects.filter(is_bot=False)
    return [sub.email for sub in admins]


def send_email_notice(message, email_to):
    subject = "Message from Develop."

    email_from = "leo@cophead567.opalstacked.com"
    send_mail(
        subject,
        message,
        email_from,
        email_to,
        fail_silently=False,
    )
    n = datetime.now()
    logger.info("Email sent at " + n.strftime("%H:%M %m-%d-%y"))
