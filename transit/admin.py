from django.contrib.gis import admin
from .models import *


class ShapefileRouteAdmin(admin.GISModelAdmin):
    list_display = ("full_name", "is_enabled", "route_color", "dir_name", "line_name", "objectid")


class GTFSRouteAdmin(admin.ModelAdmin):
    list_display = ("route_long_name", "route_id", "agency_id", "route_short_name", "route_desc", "route_type")


class TripAdmin(admin.ModelAdmin):
    list_display = ("trip_id", "route", "service_id", "trip_headsign", "shape_id", "direction_id")


class StopTimeAdmin(admin.ModelAdmin):
    list_display = ("trip", "stop_id", "stop_sequence", "arrival_time", "departure_time")


class ServiceCalendarAdmin(admin.ModelAdmin):
    list_display = ("service_id", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
                    "start_date", "end_date")


admin.site.register(ShapefileRoute, ShapefileRouteAdmin)
admin.site.register(GTFSRoute, GTFSRouteAdmin)
admin.site.register(Trip, TripAdmin)
admin.site.register(StopTime, StopTimeAdmin)
admin.site.register(ServiceCalendar, ServiceCalendarAdmin)
