"""This command is used to query the APIs, compare the results with the DB and make appropriate changes."""

import logging

from django.core.management.base import BaseCommand
from develop.models import *
from datetime import datetime

from develop.management.commands.api_scans import development_api_scan

logger = logging.getLogger("django")


class Command(BaseCommand):
    def handle(self, *args, **options):
        control = Control.objects.get(id=1)
        if control.scan:
            n = datetime.now()
            logger.info(n.strftime("%H:%M %m-%d-%y") + ": scan started.")
            development_api_scan()
            e = datetime.now()
            logger.info(e.strftime("%H:%M %m-%d-%y") + ": scan finished.")
