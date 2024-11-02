from django.contrib.gis import admin

from rpd.models import *


class DistrictsAdmin(admin.GISModelAdmin):
    list_display = ("district", "objectid", "shape_are", "zoneid")


class IncidentsAdmin(admin.GISModelAdmin):
    list_display = ("objectid", "crime_category", "crime_description", "crime_type", "reported_block_address",
                    "reported_year", "reported_month", "reported_day", "created_date", "modified_date")


admin.site.register(TrackArea, admin.GISModelAdmin)
admin.site.register(RaleighPoliceDistrict, DistrictsAdmin)
admin.site.register(Incident, IncidentsAdmin)
