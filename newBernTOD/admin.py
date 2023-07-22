from django.contrib.gis import admin

from newBernTOD.models import *


class ParcelAdmin(admin.OSMGeoAdmin):
    list_display = ("pin", "property_address", "curr_zoning", "prop_zoning", "created_date", "modified_date")


class OverlayAdmin(admin.ModelAdmin):
    list_display = ("olay_name", "OBJECTID", "overlay", "name", "created_date", "modified_date")


class NCODAdmin(admin.ModelAdmin):
    list_display = ("olay_name", "overlay", "zone_case", "objectid")


class HODAdmin(admin.ModelAdmin):
    list_display = ("olay_name", "overlay", "zone_case", "objectid")


admin.site.register(Parcel, ParcelAdmin)
admin.site.register(Overlay, OverlayAdmin)
admin.site.register(NCOD, NCODAdmin)
admin.site.register(HOD, HODAdmin)
