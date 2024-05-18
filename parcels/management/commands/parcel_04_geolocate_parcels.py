import logging
from datetime import datetime

from django.core.management.base import BaseCommand
from django.core.paginator import Paginator

from parcels.management.commands.parcel_03_convert_coordinates import get_elapsed_time
from parcels.models import ParcelHistorical, RaleighSubsection
from parcels.parcel_archive.functions import identify_coordinate_system, convert_geometry_to_epsg4326

logger = logging.getLogger("django")


class Command(BaseCommand):
    def add_arguments(self, parser):
        # parser.add_argument("-t", "--test", action="store_true", help="Run a test without making any changes.")
        pass

    def handle(self, *args, **options):
        start_time = datetime.now()
        parcels_unassigned = ParcelHistorical.objects.filter(raleighsubsection__isnull=True)
        parcel_ids = list(parcels_unassigned.values_list('id', flat=True))
        logger.info(f"There should be {parcels_unassigned.count()} parcels left unassigned.")
        print(f"There should be {parcels_unassigned.count()} parcels left unassigned.")
        paginator = Paginator(parcel_ids, 10000)
        paginator_num_pages = paginator.num_pages
        paginator_count = paginator.count
        paginator_range = paginator.page_range

        print(f"{paginator_num_pages} pages with {paginator_count} parcels total.")
        print(f"Page: ", end=" ")

        for page_number in paginator_range:
            logger.info(f"Checking page {page_number}")
            page_ids = paginator.page(page_number).object_list
            parcels = ParcelHistorical.objects.filter(id__in=page_ids)

            print(f"{page_number}", sep=" ", end=" ", flush=True)
            for parcel in parcels:
                logger.info(f"Checking {parcel}")
                if identify_coordinate_system(parcel) == "epsg:2264":
                    parcel.data_geojson["geometry"] = convert_geometry_to_epsg4326(parcel.data_geojson["geometry"])
                    parcel.save()

                overlapping_subsections = RaleighSubsection.objects.filter(geom__intersects=parcel.get_geosgeom_object())
                logger.info(f"overlapping_subsections: {overlapping_subsections}")

                if overlapping_subsections.count() == 0:
                    logger.info(f"Check {parcel} as no subsections intersect it.")
                else:
                    logger.info(f"{parcel} is being associated to sections.")
                    for subsection in overlapping_subsections:
                        logger.info(f"Adding {parcel} to {subsection}")
                        subsection.sections.add(parcel)

        # Get number of ParcelHistorical with no sections
        print("\n\nFinished parcel and subsection association run.")
        print(f"Num parcels with no sections: {ParcelHistorical.objects.filter(raleighsubsection__isnull=True).count()}")

        end_time = datetime.now()

        print(f"\nStart: {start_time}")
        print(f"End: {end_time}")
        print(f"Elapsed Time: {get_elapsed_time(start_time, end_time)}")
