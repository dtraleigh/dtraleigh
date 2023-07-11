from django.contrib import admin
from eats.models import District, Business, Snapshot, Tip, ReferenceLink, Vendor


class DistrictAdmin(admin.ModelAdmin):
    fields = ("name", "description", "link", "photo", "district_map")
    list_display = ("name", "link")


class BusinessAdmin(admin.ModelAdmin):
    list_display = ("name", "date_added", "district", "not_local", "open_date", "close_date")

    actions = ["make_not_local", "make_local"]

    def make_not_local(self, request, queryset):
        queryset.update(not_local=True)

    def make_local(self, request, queryset):
        queryset.update(not_local=False)

    make_not_local.short_description = "Mark selected as not local"
    make_local.short_description = "Mark selected as local"


class VendorAdmin(admin.ModelAdmin):
    list_display = ("name", "date_added", "food_hall", "not_local", "open_date", "close_date")

    actions = ["make_not_local", "make_local"]

    def make_not_local(self, request, queryset):
        queryset.update(not_local=True)

    def make_local(self, request, queryset):
        queryset.update(not_local=False)

    make_not_local.short_description = "Mark selected as not local"
    make_local.short_description = "Mark selected as local"


class SnapshotAdmin(admin.ModelAdmin):
    list_display = ("date", "local_business_count", "not_local_business_count")


class TipAdmin(admin.ModelAdmin):
    list_display = ("name", "district", "added", "description", "date")


class RefLinkAdmin(admin.ModelAdmin):
    list_display = ("headline", "description", "date_published", "date_created")


admin.site.register(District, DistrictAdmin)
admin.site.register(Business, BusinessAdmin)
admin.site.register(Vendor, VendorAdmin)
admin.site.register(Snapshot, SnapshotAdmin)
admin.site.register(Tip, TipAdmin)
admin.site.register(ReferenceLink, RefLinkAdmin)
