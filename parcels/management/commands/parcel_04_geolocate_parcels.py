import sys
from datetime import datetime

from django.core.management.base import BaseCommand
from django.core.paginator import Paginator

from parcels.models import ParcelHistorical, RaleighSubsection
from parcels.parcel_archive.functions import identify_coordinate_system, convert_geometry_to_epsg4326


class Command(BaseCommand):
    def add_arguments(self, parser):
        # parser.add_argument("-t", "--test", action="store_true", help="Run a test without making any changes.")
        pass

    def handle(self, *args, **options):
        start_time = datetime.now()
        # Set as needed
        parcel_subset = ParcelHistorical.objects.all()

        paginator = Paginator(parcel_subset, 10000)

        print(f"{paginator.num_pages} pages with {paginator.count} parcels total.")
        print(f"Page: ", end=" ")

        for page_number in paginator.page_range:
            page = paginator.page(page_number)
            print(f"{page_number}", sep=" ", end=" ", flush=True)
            for parcel in page.object_list:
                # If parcel has 0 associated subsections:

                if identify_coordinate_system(parcel) == "epsg:2264":
                    parcel.data_geojson["geometry"] = convert_geometry_to_epsg4326(parcel.data_geojson["geometry"])

                overlapping_subsections = RaleighSubsection.objects.filter(geom__intersects=parcel.get_geosgeom_object())

                if overlapping_subsections.count() == 0:
                    print(f"Check {parcel} as no subsections intersect it.")
                    sys.exit(1)

                #for subsection in overlapping_subsections:

                # Set parcel.sections to associate with the correct RaleighSubsection
                pass

        # Get number of ParcelHistorical with no sections

        print(f"Start: {start_time}")
        print(f"End: {datetime.now()}")
