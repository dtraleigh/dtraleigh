from django.contrib.gis import admin

from buildings.models import *


class BuildingAdmin(admin.GISModelAdmin):
    list_display = ("PIN_NUM", "ADDR1", "YEAR_BUILT", "LAND_VAL", "DEED_ACRES", "PROPDESC")


class DecadeAdmin(admin.GISModelAdmin):
    list_display = ("decade_name", "start_year", "end_year")


class BorderAdmin(admin.GISModelAdmin):
    list_display = ("muni_name", "created_date")


class CustomMapAdmin(admin.ModelAdmin):
    list_display = ("map_name", "created_date")


admin.site.register(Building, BuildingAdmin)
admin.site.register(Decade, DecadeAdmin)
admin.site.register(Border, BorderAdmin)
admin.site.register(CustomMap, CustomMapAdmin)
