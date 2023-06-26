import logging

from django.core.management.base import BaseCommand

from newBernTOD.models import Overlay, NCOD

logger = logging.getLogger("django")


class Command(BaseCommand):
    def handle(self, *args, **options):
        # Create a custom Overlay using the NCOD pieces from model NCOD
        # Mordecai has 3 pieces
        if not Overlay.objects.filter(olay_name="Mordecai").exists():
            mordecai_overlay = Overlay.objects.create(olay_name="Mordecai",
                                                      name="Mordecai",
                                                      overlay="NCOD",
                                                      description="Combined overlay with all mordecai pieces")

            mordecai_pieces = NCOD.objects.filter(olay_name__contains="Mordecai")

            combined_parcel_list = []
            for ncod_piece in mordecai_pieces:
                combined_parcel_list += [parcel for parcel in ncod_piece.parcels.all()]

            for parcel in combined_parcel_list:
                mordecai_overlay.parcels.add(parcel)

        # New Bern - Edenton has 2 pieces
        if not Overlay.objects.filter(olay_name="New Bern - Edenton").exists():
            nbe_overlay = Overlay.objects.create(olay_name="New Bern - Edenton",
                                                 name="New Bern - Edenton",
                                                 overlay="NCOD",
                                                 description="Combined overlay with all New Bern - Edenton pieces")

            nbe_pieces = NCOD.objects.filter(olay_name__contains="New Bern - Edenton")

            combined_parcel_list = []
            for ncod_piece in nbe_pieces:
                combined_parcel_list += [parcel for parcel in ncod_piece.parcels.all()]

            for parcel in combined_parcel_list:
                nbe_overlay.parcels.add(parcel)
