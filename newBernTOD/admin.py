from django.contrib.gis import admin

from newBernTOD.models import *


class ParcelAdmin(admin.OSMGeoAdmin):
    list_display = ("pin", "property_address", "curr_zoning", "prop_zoning")


class OverlayAdmin(admin.ModelAdmin):
    list_display = ("OLAY_NAME", "OBJECTID", "OVERLAY", "name", "created_date", "modified_date")


admin.site.register(Parcel, ParcelAdmin)
admin.site.register(Overlay, OverlayAdmin)
