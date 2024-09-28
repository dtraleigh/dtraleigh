from django.contrib.gis import admin
from .models import BusRoute


class BusRouteAdmin(admin.OSMGeoAdmin):
    list_display = ("full_name", "dir_name", "line_name", "objectid")


admin.site.register(BusRoute, BusRouteAdmin)
