"""This command is used to notify subscribers of changes in the last hour"""
import logging
from datetime import datetime
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from develop.models import *
from develop.management.commands.location import *
from develop.management.commands.actions import create_new_discourse_post
from develop.management.commands.actions import reset_skipped_updates
from develop.management.commands.actions import send_skipped_update_digest
from develop.management.commands.emails import *

logger = logging.getLogger("django")


def get_everything_that_changed():
    # Plans to deprecate this soon as we will move away from scanning for changes in the last hour.
    ######
    # Get everything that has changed in the last hour
    everything_that_changed = []

    # Let's exclude Development changes for now as we need to review the API content due to possible changes.
    # devs_that_changed = DevelopmentPlan.objects.filter(modified_date__range=[timezone.now() - timedelta(hours=1),
    #                                                                          timezone.now()])
    SRs_that_changed = SiteReviewCase.objects.filter(modified_date__range=[timezone.now() - timedelta(hours=1),
                                                                           timezone.now()])
    zons_that_changed = Zoning.objects.filter(modified_date__range=[timezone.now() - timedelta(hours=1),
                                                                    timezone.now()])
    AADs_that_changed = AdministrativeAlternate.objects.filter(modified_date__range=[timezone.now() -
                                                                                     timedelta(hours=1),
                                                                                     timezone.now()])
    TCs_that_changed = TextChangeCase.objects.filter(modified_date__range=[timezone.now() -
                                                                           timedelta(hours=1),
                                                                           timezone.now()])
    NMs_that_changed = NeighborhoodMeeting.objects.filter(modified_date__range=[timezone.now() -
                                                                                timedelta(hours=1),
                                                                                timezone.now()])
    DACs_that_changed = DesignAlternateCase.objects.filter(modified_date__range=[timezone.now() -
                                                                                timedelta(hours=1),
                                                                                timezone.now()])

    # for dev in devs_that_changed:
    #     everything_that_changed.append(dev)
    for SR in SRs_that_changed:
        everything_that_changed.append(SR)
    for AAD in AADs_that_changed:
        everything_that_changed.append(AAD)
    for TC in TCs_that_changed:
        everything_that_changed.append(TC)
    for zon in zons_that_changed:
        everything_that_changed.append(zon)
    for nm in NMs_that_changed:
        everything_that_changed.append(nm)
    for DAC in DACs_that_changed:
        everything_that_changed.append(DAC)

    return everything_that_changed


class Command(BaseCommand):
    def handle(self, *args, **options):
        n = datetime.now().strftime("%H:%M %m-%d-%y")
        control = Control.objects.get(id=1)

        if not control.notify:
            logger.info(f"{n}: Notify skipped - turned off in Control.")
            return

        logger.info(f"{n}: Notify started.")

        everything_that_changed = get_everything_that_changed()

        if not everything_that_changed:
            logger.info("Notify finished. Nothing changed in the last hour.")
            return

        logger.info(f"{str(len(everything_that_changed))} item(s) changed in the last hour: "
                    f"{str([str(item) for item in everything_that_changed])}")

        # We need to filter everything_that_changed for only the cover areas that each user is subscribed to.
        # We also need to include None. Rather than pass literally everything_that_changed let's filter it
        # for each user and then send them an email.
        all_active_subscribers = Subscriber.objects.filter(send_emails=True)

        reset_skipped_updates()

        try:
            for subscriber in all_active_subscribers:
                # Take everything_that_changed and get the items that we want to post to discourse
                covered_items = get_itb_items(everything_that_changed)

                if not subscriber.is_bot:
                    continue

                logger.info(f"{str(len(covered_items))} of those are inside the beltline "
                            f"for {str(subscriber.name)}.")

                # Post to discourse community
                for item in covered_items:
                    logger.info(f"Posting {item._meta.verbose_name} ({str(item)}) to Discourse "
                                f"for {str(subscriber.name)}.")
                    create_new_discourse_post(subscriber, item)
        finally:
            send_skipped_update_digest()

        logger.info("Notify finished.")
