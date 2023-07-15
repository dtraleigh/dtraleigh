from datetime import datetime

from django.core.management.base import BaseCommand
from rpd.models import *
from rpd.functions import is_glenwood_south
from rpd.management.commands.scan_incidents import get_incidents_for_month, save_incidents_to_db


def refresh_is_glenwood_south():
    all_incidents = Incident.objects.all()

    for incident in all_incidents:
        incident.is_glenwood_south = is_glenwood_south(incident)
        incident.save()


class Command(BaseCommand):
    def handle(self, *args, **options):
        today = datetime.today()
        incidents = get_incidents_for_month(today.year, today.month)
        save_incidents_to_db(incidents)
        refresh_is_glenwood_south()
