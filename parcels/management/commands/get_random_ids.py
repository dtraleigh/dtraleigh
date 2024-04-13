import random

from django.core.management.base import BaseCommand
from django.core.paginator import Paginator

from parcels.models import ParcelHistorical


class Command(BaseCommand):
    def add_arguments(self, parser):
        # parser.add_argument("-t", "--test", action="store_true", help="Run a test without making any changes.")
        pass

    def handle(self, *args, **options):
        parcel_subset = ParcelHistorical.objects.all()
        paginator = Paginator(parcel_subset, 10000)
        all_random_ids = []

        for page_number in paginator.page_range:
            page = paginator.page(page_number)
            random_parcels_from_this_page = random.sample(list(page.object_list), 35)
            all_random_ids += [p.id for p in random_parcels_from_this_page]

        print(all_random_ids)
