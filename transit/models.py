from django.contrib.gis.db import models


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

    def __str__(self):
        return self.full_name or self.route_long_name or self.route_short_name

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
