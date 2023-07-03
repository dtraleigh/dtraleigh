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

# Not using this right now so will comment out. There are bugs here to work out if you decide to bring back. Feb 2022
# def create_email_message(items_that_changed):
#     # /// Header
#     email_header = "=========================\n"
#     email_header += "The latest updates from\n"
#     email_header += "THE RALEIGH WIRE SERVICE\n"
#
#     if settings.DEVELOP_INSTANCE == "Develop":
#         email_header += "[Develop version]\n"
#     email_header += "=========================\n\n"
#
#     # \\\\ End Header
#
#     # //// New Devs Section
#     # If the dev's created date was in the last hour, we assume it's a new dev
#     new_devs = []
#     updated_devs = []
#     new_zons = []
#     updated_zons = []
#
#     for item in items_that_changed:
#         if isinstance(item, DevelopmentPlan) or isinstance(item, SiteReviewCase):
#             if item.created_date > timezone.now() - timedelta(hours=1):
#                 new_devs.append(item)
#             else:
#                 updated_devs.append(item)
#         if isinstance(item, Zoning):
#             if item.created_date > timezone.now() - timedelta(hours=1):
#                 new_zons.append(item)
#             else:
#                 updated_zons.append(item)
#
#     # /// New Devs section
#
#     if new_devs:
#         new_devs_message = "--------------New Developments---------------\n\n"
#         for new_dev in new_devs:
#             new_devs_message += get_new_dev_text(new_dev)
#     else:
#         new_devs_message = ""
#
#     # \\\ End New Devs Section
#
#     # /// Dev Updates Section
#
#     if updated_devs:
#         updated_devs_message = "-------------Existing Dev Updates------------\n\n"
#         for updated_dev in updated_devs:
#             updated_devs_message += get_updated_dev_text(updated_dev)
#     else:
#         updated_devs_message = ""
#
#     # \\\ End Dev Updates Section
#
#     # /// New Zons section
#
#     if new_zons:
#         new_zons_message = "-----------New Zoning Requests------------\n\n"
#         for new_zon in new_zons:
#             new_zons_message += get_new_zon_text(new_zon)
#     else:
#         new_zons_message = ""
#
#     # \\\ End New Devs Section
#
#     # /// Dev Updates Section
#
#     if updated_zons:
#         updated_zons_message = "--------Existing Zoning Request Updates-------\n\n"
#         for updated_zon in updated_zons:
#             updated_zons_message += get_updated_zon_text(updated_zon)
#     else:
#         updated_zons_message = ""
#
#     # \\\ End Dev Updates Section
#
#     # /// Footer
#     email_footer = "*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*\n"
#     try:
#         email_footer += get_status_legend_text() + "\n\n"
#     except AttributeError:
#         email_footer += "Please see the Current Development Activity website for status abbreviations.\n\n"
#     email_footer += "You are subscribed to THE RALEIGH WIRE SERVICE\n"
#     email_footer += "This is a service of DTRaleigh.com\n"
#     email_footer += "*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*\n"
#
#     # \\\ End Footer
#
#     message = email_header + new_devs_message + updated_devs_message + new_zons_message + \
#               updated_zons_message + email_footer
#
#     return message
