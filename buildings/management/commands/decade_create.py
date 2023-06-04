"""This is used to create the decades in a scripted fashion. Will only run this once."""
from django.core.management.base import BaseCommand
from buildings.models import *
from django.contrib.gis.geos import MultiPolygon


class Command(BaseCommand):
    def handle(self, *args, **options):
        create_decades()
        update_decades()


def create_decades():
    # """Let's create decades between 1700 and 2019"""
    # start_year = 1700
    # end_year = 2019
    start_year = 2020
    end_year = 2029

    while start_year < end_year:
        decade_start = start_year
        decade_end = start_year + 9
        decade_name = f"{str(start_year)}s"

        Decade.objects.create(start_year=decade_start,
                              end_year=decade_end,
                              decade_name=decade_name)

        start_year += 10


def update_decades():
    decades = Decade.objects.all()

    for decade in decades:
        bldgs_in_decade = Building.objects.filter(YEAR_BUILT__range=(decade.start_year, decade.end_year))
        mp = MultiPolygon([p.geom for p in bldgs_in_decade])
        decade.geom = mp
        decade.save()
