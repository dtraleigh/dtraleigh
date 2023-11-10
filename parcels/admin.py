from django.contrib.gis import admin

from parcels.models import Parcel


class ParcelAdmin(admin.OSMGeoAdmin):
    list_display = ("objectid", "is_active", "pin", "addr1", "propdesc", "created_date",
                    "modified_date")


admin.site.register(Parcel, ParcelAdmin)
