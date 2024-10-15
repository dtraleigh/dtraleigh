from django.contrib.gis.db import models
from datetime import datetime, timedelta


class ShapefileRoute(models.Model):
    PURPLE = "rgb(86, 53, 130)"
    ORANGE = "rgb(234, 133, 23)"
    RED = "rgb(217, 42, 28)"
    BLUE = "rgb(0, 134, 196)"
    MAGENTA = "rgb(157, 68, 137)"
    WHITE = "rgb(255, 255, 255)"
    GREEN = "rgb(4, 150, 132)"
    COLORS = (
        (PURPLE, "Purple"),
        (ORANGE, "Orange"),
        (RED, "Red"),
        (BLUE, "Blue"),
        (MAGENTA, "Magenta"),
        (WHITE, "White"),
        (GREEN, "Green"),
    )

    objectid = models.IntegerField()
    full_name = models.CharField(max_length=50, null=True, blank=True)
    dir_id = models.CharField(max_length=1, null=True, blank=True)
    dir_name = models.CharField(max_length=10, null=True, blank=True)
    pattern = models.CharField(max_length=1, null=True, blank=True)
    line_name = models.CharField(max_length=35, null=True, blank=True)
    map_name = models.CharField(max_length=14, null=True, blank=True)
    shape_len = models.CharField(max_length=1, null=True, blank=True)
    geom = models.MultiLineStringField(srid=4326, null=True, blank=True)
    route_color = models.CharField(max_length=30, choices=COLORS, default=RED)
    is_enabled = models.BooleanField(default=True)

    def __str__(self):
        return self.full_name or f"ShapefileRoute {self.objectid}"

    class Meta:
        ordering = ["full_name"]


busroute_mapping = {
    'objectid': 'OBJECTID',
    'full_name': 'full_name',
    'dir_id': 'dir_id',
    'dir_name': 'dir_name',
    'pattern': 'pattern',
    'line_name': 'line_name',
    'map_name': 'map_name',
    'shape_len': 'Shape__Len',
    'geom': 'MULTILINESTRING25D',
}


class GTFSRoute(models.Model):
    route_id = models.CharField(max_length=255, unique=True)
    agency_id = models.CharField(max_length=255, null=True, blank=True)
    route_short_name = models.CharField(max_length=50, null=True, blank=True)
    route_long_name = models.CharField(max_length=255, null=True, blank=True)
    route_desc = models.TextField(null=True, blank=True)
    route_type = models.IntegerField(null=True, blank=True)
    shapefile_routes = models.ManyToManyField('ShapefileRoute', blank=True)

    def __str__(self):
        return self.route_long_name or self.route_short_name

    class Meta:
        ordering = ["route_long_name"]

    def get_route_start_stop(self, day_of_week, direction_id):
        """
        Returns the stop_id for the first stop of the route for a specific day of the week and direction.

        :param day_of_week: 'monday', 'tuesday', 'wednesday', etc.
        :param direction_id: 0 for outbound, 1 for inbound.
        :return: The stop_id of the route start, or None if not found.
        """
        trips = self.trip_set.filter(direction_id=direction_id)  # Filter by direction
        for trip in trips:
            # Filter trips by the service running on the specified day
            service_calendar = ServiceCalendar.objects.get(service_id=trip.service_id)
            if getattr(service_calendar, day_of_week):
                # Get the first stop_time for the trip, ordered by stop_sequence
                first_stop_time = StopTime.objects.filter(trip=trip).order_by('stop_sequence').first()
                if first_stop_time:
                    return first_stop_time.stop_id
        return None

    def get_route_end_stop(self, day_of_week, direction_id):
        """
        Returns the stop_id for the last stop of the route for a specific day of the week and direction.

        :param day_of_week: 'monday', 'tuesday', 'wednesday', etc.
        :param direction_id: 0 for outbound, 1 for inbound.
        :return: The stop_id of the route end, or None if not found.
        """
        trips = self.trip_set.filter(direction_id=direction_id)  # Filter by direction
        for trip in trips:
            # Filter trips by the service running on the specified day
            service_calendar = ServiceCalendar.objects.get(service_id=trip.service_id)
            if getattr(service_calendar, day_of_week):
                # Get the last stop_time for the trip, ordered by stop_sequence in descending order
                last_stop_time = StopTime.objects.filter(trip=trip).order_by('-stop_sequence').first()
                if last_stop_time:
                    return last_stop_time.stop_id
        return None

    def get_all_departure_times_at_start(self, day_of_week, direction_id):
        """
        Returns a sorted list of departure times for the first stop of the route on a specific day of the week
        and direction.

        :param day_of_week: 'monday', 'tuesday', 'wednesday', etc.
        :param direction_id: 0 for outbound, 1 for inbound.
        :return: A sorted list of departure times for the starting stop.
        """
        departure_times = []

        trips = self.trip_set.filter(direction_id=direction_id)  # Filter by direction
        for trip in trips:
            service_calendar = ServiceCalendar.objects.get(service_id=trip.service_id)
            if getattr(service_calendar, day_of_week):
                first_stop_time = StopTime.objects.filter(trip=trip).order_by('stop_sequence').first()
                if first_stop_time:
                    departure_times.append(first_stop_time.departure_time)

        return sorted(departure_times)

    def is_high_frequency(self, day_of_week):
        """
        Determines if there are any departure times at the starting stop for the route
        that are within 15 minutes or less of each other for outbound trips first
        and inbound trips next.

        :param day_of_week: 'monday', 'tuesday', 'wednesday', etc.
        :return: True if high frequency exists, otherwise False.
        """
        outbound_departure_times = self.get_all_departure_times_at_start(day_of_week, direction_id=0)
        if self._has_high_frequency(outbound_departure_times):
            return True

        inbound_departure_times = self.get_all_departure_times_at_start(day_of_week, direction_id=1)
        if self._has_high_frequency(inbound_departure_times):
            return True

        return False

    def _has_high_frequency(self, departure_times):
        """
        Helper method to determine if any time differences are 15 minutes or less.

        :param departure_times: List of departure times.
        :return: True if high frequency exists, otherwise False.
        """
        departure_times.sort()

        for i in range(1, len(departure_times)):
            t1 = datetime.combine(datetime.today(), departure_times[i - 1])
            t2 = datetime.combine(datetime.today(), departure_times[i])
            if (t2 - t1) <= timedelta(minutes=15):
                return True

        return False

    def print_all_trips_with_first_stop_time(self, day_of_week):
        """
        Prints a list of all trips associated with this GTFSRoute, each trip's first stop time,
        stop sequence, and stop ID for the given day of the week, sorted by the first stop time.
        :param day_of_week: 'monday', 'tuesday', 'wednesday', etc.
        """
        trips = self.trip_set.all()
        trip_times = []

        for trip in trips:
            try:
                service_calendar = ServiceCalendar.objects.get(service_id=trip.service_id)

                if getattr(service_calendar, day_of_week):
                    first_stop_time = StopTime.objects.filter(trip=trip).order_by('stop_sequence').first()

                    if first_stop_time:
                        trip_times.append((
                            trip.trip_id,
                            first_stop_time.stop_id,
                            first_stop_time.departure_time,
                            first_stop_time.stop_sequence
                        ))
            except ServiceCalendar.DoesNotExist:
                continue

        trip_times.sort(key=lambda x: x[2])

        for trip_id, stop_id, departure_time, stop_sequence in trip_times:
            print(
                f"Trip ID: {trip_id}, Stop ID: {stop_id}, First Stop Time: {departure_time.strftime('%H:%M:%S')}, Stop Sequence: {stop_sequence}")


class Trip(models.Model):
    trip_id = models.CharField(max_length=255, primary_key=True)
    route = models.ForeignKey(GTFSRoute, on_delete=models.CASCADE)  # FK to Route
    service_id = models.CharField(max_length=255)
    trip_headsign = models.CharField(max_length=255, blank=True, null=True)
    shape_id = models.CharField(max_length=255, blank=True, null=True)
    direction_id = models.IntegerField()


class StopTime(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    stop_id = models.CharField(max_length=255)
    stop_sequence = models.IntegerField()
    arrival_time = models.TimeField()  # Be cautious if handling times > 24:00
    departure_time = models.TimeField()


class ServiceCalendar(models.Model):
    service_id = models.CharField(max_length=255, unique=True)
    monday = models.BooleanField(default=False)
    tuesday = models.BooleanField(default=False)
    wednesday = models.BooleanField(default=False)
    thursday = models.BooleanField(default=False)
    friday = models.BooleanField(default=False)
    saturday = models.BooleanField(default=False)
    sunday = models.BooleanField(default=False)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return self.service_id
