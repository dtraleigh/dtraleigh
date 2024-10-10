import csv
from django.core.management.base import BaseCommand
from django.db import transaction
from transit.models import Trip, StopTime, GTFSRoute

# python manage.py import_gtfs --test --routes=transit/gtfs-sept-9/routes.txt --trips=transit/gtfs-sept-9/trips.txt --stop_times=transit/gtfs-sept-9/stop_times.txt

from datetime import time, timedelta


def normalize_time(gtfs_time):
    """
    Converts a time like '24:30:00' into '00:30:00' of the next day.
    """
    hours, minutes, seconds = map(int, gtfs_time.split(':'))

    if hours >= 24:
        # Reduce 24 hours and return the adjusted time
        hours = hours - 24
        # You can store this extra day information somewhere if needed
    return time(hour=hours, minute=minutes, second=seconds)


class Command(BaseCommand):
    help = "Import GTFS data from text files into the database."

    def add_arguments(self, parser):
        parser.add_argument(
            '--test', action='store_true', help='Run the command without committing changes to the database'
        )
        parser.add_argument('--routes', required=True, help='Path to routes.txt file')
        parser.add_argument('--trips', required=True, help='Path to trips.txt file')
        parser.add_argument('--stop_times', required=True, help='Path to stop_times.txt file')

    def handle(self, *args, **options):
        routes_file = options['routes']
        trips_file = options['trips']
        stop_times_file = options['stop_times']
        test_run = options['test']

        if test_run:
            self.stdout.write(self.style.WARNING('Running in test mode. No changes will be made.'))

        try:
            with transaction.atomic():
                self.import_routes(routes_file)
                self.import_trips(trips_file)
                self.import_stop_times(stop_times_file)

                if test_run:
                    raise transaction.TransactionManagementError("Test run completed. Rolling back changes.")

        except transaction.TransactionManagementError:
            self.stdout.write(self.style.SUCCESS('Test run completed successfully. No changes made.'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))

    def import_routes(self, routes_file):
        with open(routes_file, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                gtfs_route, created = GTFSRoute.objects.update_or_create(
                    route_id=row['route_id'],
                    defaults={
                        'agency_id': row['agency_id'],
                        'route_short_name': row['route_short_name'],
                        'route_long_name': row['route_long_name'],
                        'route_desc': row.get('route_desc', ''),
                        'route_type': row['route_type'],
                    }
                )
                self.stdout.write(f'Processed GTFSRoute: {gtfs_route.route_id}')

    def import_trips(self, trips_file):
        with open(trips_file, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                route = GTFSRoute.objects.get(route_id=row['route_id'])
                trip, created = Trip.objects.update_or_create(
                    trip_id=row['trip_id'],
                    defaults={
                        'route': route,
                        'service_id': row['service_id'],
                        'trip_headsign': row['trip_headsign'],
                        'shape_id': row.get('shape_id', ''),
                        'direction_id': row.get('direction_id', 0),
                    }
                )
                self.stdout.write(f'Processed Trip: {trip.trip_id}')

    def import_stop_times(self, stop_times_file):
        with open(stop_times_file, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                trip = Trip.objects.get(trip_id=row['trip_id'])
                stop_time, created = StopTime.objects.update_or_create(
                    trip=trip,
                    stop_id=row['stop_id'],
                    stop_sequence=row['stop_sequence'],
                    defaults={
                        'arrival_time': normalize_time(row['arrival_time']),
                        'departure_time': normalize_time(row['departure_time']),
                    }
                )
                self.stdout.write(f'Processed StopTime for trip: {trip.trip_id}, stop: {stop_time.stop_id}')
