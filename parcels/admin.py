from django.contrib.gis import admin

from parcels.models import Parcel, Snapshot, ParcelHistorical, RaleighSubsection


class ParcelAdmin(admin.GISModelAdmin):
    list_display = ("objectid", "is_active", "pin", "addr1", "addr2", "addr3", "propdesc", "created_date",
                    "modified_date")


class SnapshotAdmin(admin.GISModelAdmin):
    list_display = ("name", "created_date", "modified_date")


class ParcelHistoricalAdmin(admin.GISModelAdmin):
    list_display = ("id", "created_date", "modified_date")


class RaleighSubsectionAdmin(admin.GISModelAdmin):
    list_display = ("id", "created_date", "modified_date")
    raw_id_fields = ("sections",)


admin.site.register(Parcel, ParcelAdmin)
admin.site.register(Snapshot, SnapshotAdmin)
admin.site.register(ParcelHistorical, ParcelHistoricalAdmin)
admin.site.register(RaleighSubsection, RaleighSubsectionAdmin)