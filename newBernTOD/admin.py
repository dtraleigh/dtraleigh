from django.contrib.gis import admin

from newBernTOD.models import *


class ParcelAdmin(admin.OSMGeoAdmin):
    list_display = ("pin", "property_address", "curr_zoning", "prop_zoning")


admin.site.register(Parcel, ParcelAdmin)
