from django.core.management.base import BaseCommand
from develop.models import *
from develop.management.commands.location import *
from develop.management.commands.actions import create_new_discourse_post
from develop.management.commands.emails import *


class Command(BaseCommand):
    def handle(self, *args, **options):
        devbot = Subscriber.objects.get(id=3)

        test_items_update = [
            # Zoning.objects.get(id=2066),
            # TextChangeCase.objects.get(id=72),
            # AdministrativeAlternate.objects.get(id=220),
            # SiteReviewCase.objects.get(id=939),
            NeighborhoodMeeting.objects.get(id=853)
            # DesignAlternateCase.objects.get(id=25)
        ]

        for item in test_items_update:
            create_new_discourse_post(devbot, item)

        # Temp data
        test_items_new = []
        # temp_zoning_case = Zoning.objects.create(zpyear=2022,
        #                                          zpnum=38,
        #                                          status="Received 2-2-22; under review until 2-16-22.",
        #                                          location="208 Freeman Street",
        #                                          received_by="contact",
        #                                          plan_url="https://cityofraleigh0drupal.blob.core.usgovcloudapi.net/drupal-prod/COR22/Z-013-22.pdf",
        #                                          location_url="https://maps.raleighnc.gov/iMAPS/?pin=0796487963")
        # test_items_new.append(temp_zoning_case)
        # temp_tcc = TextChangeCase.objects.create(case_number="TC-XX-22",
        #                                          case_url="https://cityofraleigh0drupal.blob.core.usgovcloudapi.net/drupal-prod/COR22/TC-20-21.pdf",
        #                                          project_name="project_name",
        #                                          status="status")
        # test_items_new.append(temp_tcc)
        # temp_aad = AdministrativeAlternate.objects.create(case_number="AAD-XX-22",
        #                                                   case_url="https://cityofraleigh0drupal.blob.core.usgovcloudapi.net/drupal-prod/COR15/AAD-017-21.pdf",
        #                                                   project_name="project_name",
        #                                                   status="status")
        # test_items_new.append(temp_aad)
        # temp_src = SiteReviewCase.objects.create(case_number="ASR-XXX-2022",
        #                                          case_url="https://cityofraleigh0drupal.blob.core.usgovcloudapi.net/drupal-prod/COR15/ASR-0007-2022.pdf",
        #                                          project_name="project_name",
        #                                          status="status")
        # test_items_new.append(temp_src)
        temp_nm = NeighborhoodMeeting.objects.create(meeting_datetime_details="Feb. 22, 6:00 p.m.",
                                                     meeting_location="208 Freeman Street",
                                                     rezoning_site_address="2000 Martin Street",
                                                     rezoning_site_address_url="https://cityofraleigh0drupal.blob.core.usgovcloudapi.net/drupal-prod/COR22/208FreemanStreet.pdf"
                                                     )
        test_items_new.append(temp_nm)
        # temp_dac = DesignAlternateCase.objects.create(case_number="DA-0032-1021",
        #                                               case_url="https://cityofraleigh0drupal.blob.core.usgovcloudapi.net/drupal-prod/COR15/DA-0032-1021.pdf",
        #                                               project_name="test DAC name",
        #                                               status="some status")
        # test_items_new.append(temp_dac)

        for item in test_items_new.copy():
            create_new_discourse_post(devbot, item)
            item.delete()
