from django.contrib.gis import admin

from parcels.models import Parcel


class ParcelAdmin(admin.OSMGeoAdmin):
    list_display = ("objectid", "is_active", "pin", "property_address", "curr_zoning", "prop_zoning", "created_date", "modified_date")


admin.site.register(Parcel, ParcelAdmin)
