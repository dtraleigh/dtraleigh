from django.contrib.gis import admin

from parcels.models import Parcel, Snapshot, ParcelHistorical


class ParcelAdmin(admin.OSMGeoAdmin):
    list_display = ("objectid", "is_active", "pin", "addr1", "addr2", "addr3", "propdesc", "created_date",
                    "modified_date")


class SnapshotAdmin(admin.OSMGeoAdmin):
    list_display = ("name", "created_date", "modified_date")


class ParcelHistoricalAdmin(admin.OSMGeoAdmin):
    list_display = ("id", "created_date", "modified_date")


admin.site.register(Parcel, ParcelAdmin)
admin.site.register(Snapshot, SnapshotAdmin)
admin.site.register(ParcelHistorical, ParcelHistoricalAdmin)
