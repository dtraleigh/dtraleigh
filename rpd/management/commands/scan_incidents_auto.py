from datetime import datetime

from django.core.management.base import BaseCommand
from rpd.models import *
from rpd.functions import is_glenwood_south
from rpd.management.commands.scan_incidents import get_downtown_incidents_for_month, save_incidents_to_db
from newBernTOD.functions import send_email_notice


def refresh_is_glenwood_south():
    all_incidents = Incident.objects.all()

    for incident in all_incidents:
        incident.is_glenwood_south = is_glenwood_south(incident)
        incident.save()


class Command(BaseCommand):
    def handle(self, *args, **options):
        today = datetime.today()
        report = f"RPD incidents for {today.strftime('%B, %Y')}\n"

        incidents = get_downtown_incidents_for_month(today.year, today.month)
        report += f"    * {len(incidents)} incidents in downtown.\n"

        new_downtown_incidents, new_glenwood_south_incidents = save_incidents_to_db(incidents)
        report += f"Daily Additions:\n"
        report += f"    * New Downtown Incidents: {len(new_downtown_incidents)}\n"
        report += f"    * New Glenwood Incidents: {len(new_glenwood_south_incidents)}\n"

        subject = "Message from RPD"
        send_email_notice(subject, report, ["leo@dtraleigh.com"])
        refresh_is_glenwood_south()
