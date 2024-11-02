from django.contrib.gis.db import models
from datetime import datetime, timedelta


class ShapefileRoute(models.Model):
    objectid = models.IntegerField()
    full_name = models.CharField(max_length=50, null=True, blank=True)
    dir_id = models.CharField(max_length=1, null=True, blank=True)
    dir_name = models.CharField(max_length=10, null=True, blank=True)
    pattern = models.CharField(max_length=1, null=True, blank=True)
    line_name = models.CharField(max_length=35, null=True, blank=True)
    map_name = models.CharField(max_length=14, null=True, blank=True)
    shape_len = models.CharField(max_length=1, null=True, blank=True)
    geom = models.MultiLineStringField(srid=4326, null=True, blank=True)
    route_color = models.CharField(max_length=30, null=True, blank=True)
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
    is_enabled = models.BooleanField(default=True)

    def __str__(self):
        return self.route_long_name or self.route_short_name

    class Meta:
        ordering = ["route_long_name"]

    def get_route_start_stop(self, day_of_week, direction_id):
        """
        Returns the stop_id for the first stop of the route for a specific day of the week and direction.
        """
        trips = self.trip_set.filter(direction_id=direction_id)
        for trip in trips:
            service_calendar = ServiceCalendar.objects.get(service_id=trip.service_id)
            if getattr(service_calendar, day_of_week):
                first_stop_time = StopTime.objects.filter(trip=trip).order_by('stop_sequence').first()
                if first_stop_time:
                    return first_stop_time.stop_id
        return None

    def get_route_end_stop(self, day_of_week, direction_id):
        """
        Returns the stop_id for the last stop of the route for a specific day of the week and direction.
        """
        trips = self.trip_set.filter(direction_id=direction_id)
        for trip in trips:
            service_calendar = ServiceCalendar.objects.get(service_id=trip.service_id)
            if getattr(service_calendar, day_of_week):
                last_stop_time = StopTime.objects.filter(trip=trip).order_by('-stop_sequence').first()
                if last_stop_time:
                    return last_stop_time.stop_id
        return None

    def get_valid_trips(self, day_of_week, direction_id):
        """
        Filters and returns only those trips that serve the entire route (i.e., start at the first stop
        and end at the last stop for the route).
        """
        valid_trips = []
        start_stop_id = self.get_route_start_stop(day_of_week, direction_id)
        end_stop_id = self.get_route_end_stop(day_of_week, direction_id)

        if not start_stop_id or not end_stop_id:
            return valid_trips  # No valid start or end stop found

        trips = self.trip_set.filter(direction_id=direction_id)
        for trip in trips:
            service_calendar = ServiceCalendar.objects.get(service_id=trip.service_id)
            if getattr(service_calendar, day_of_week):
                first_stop_time = StopTime.objects.filter(trip=trip).order_by('stop_sequence').first()
                last_stop_time = StopTime.objects.filter(trip=trip).order_by('-stop_sequence').first()

                if first_stop_time and last_stop_time:
                    if first_stop_time.stop_id == start_stop_id and last_stop_time.stop_id == end_stop_id:
                        valid_trips.append(trip)

        return valid_trips

    def get_all_departure_times_at_start(self, day_of_week, direction_id):
        """
        Returns a sorted list of departure times for valid trips that serve the entire route
        for the first stop of the route on a specific day of the week and direction.
        """
        departure_times = []
        valid_trips = self.get_valid_trips(day_of_week, direction_id)

        for trip in valid_trips:
            first_stop_time = StopTime.objects.filter(trip=trip).order_by('stop_sequence').first()
            if first_stop_time:
                departure_times.append(first_stop_time.departure_time)

        return sorted(departure_times)

    def start_high_frequency(self, day_of_week):
        """
        Returns the start time of the high-frequency service period on a given day of the week,
        considering only trips that serve the entire route.
        """
        outbound_departure_times = self.get_all_departure_times_at_start(day_of_week, direction_id=0)
        inbound_departure_times = self.get_all_departure_times_at_start(day_of_week, direction_id=1)

        outbound_start, _ = self._find_high_frequency_times(outbound_departure_times)
        inbound_start, _ = self._find_high_frequency_times(inbound_departure_times)

        if outbound_start and inbound_start:
            return min(outbound_start, inbound_start)
        return outbound_start or inbound_start

    def stop_high_frequency(self, day_of_week):
        """
        Returns the end time of the high-frequency service period on a given day of the week,
        considering only trips that serve the entire route.
        """
        outbound_departure_times = self.get_all_departure_times_at_start(day_of_week, direction_id=0)
        inbound_departure_times = self.get_all_departure_times_at_start(day_of_week, direction_id=1)

        _, outbound_end = self._find_high_frequency_times(outbound_departure_times)
        _, inbound_end = self._find_high_frequency_times(inbound_departure_times)

        if outbound_end and inbound_end:
            return max(outbound_end, inbound_end)
        return outbound_end or inbound_end

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

    def _find_high_frequency_times(self, departure_times):
        """
        Helper method to find the start and end times of high-frequency service (within 15 minutes).
        Returns None if no high-frequency period is found.
        """
        if len(departure_times) < 2:
            return None, None  # Not enough data for high-frequency service

        start_time = None
        end_time = None

        for i in range(1, len(departure_times)):
            t1 = datetime.combine(datetime.today(), departure_times[i - 1])
            t2 = datetime.combine(datetime.today(), departure_times[i])

            if (t2 - t1) <= timedelta(minutes=15):
                if not start_time:
                    start_time = departure_times[i - 1]
                end_time = departure_times[i]
            elif start_time and end_time:
                # Break once we no longer find high-frequency times
                break

        return start_time, end_time

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
