import logging

from django.core.management.base import BaseCommand
from datetime import datetime

from develop.management.commands.emails import *

logger = logging.getLogger("django")


class Command(BaseCommand):
    def handle(self, *args, **options):
        n = datetime.now().strftime("%H:%M %m-%d-%y")
        logger.info(f"{n}: Trying to send email to admins")
        message = "Email from test_email.py"
        send_email_notice(message, email_admins())
        e = datetime.now().strftime("%H:%M %m-%d-%y")
        logger.info(f"{e}: Sent test email to admins")
