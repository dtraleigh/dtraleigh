from django.contrib import admin
from parking.models import Rate, ParkingLocation, RateSchedule


class RateAdmin(admin.ModelAdmin):
    save_as = True
    list_display = ("day_of_week", "is_free", "all_day", "rate", "start_time", "end_time")


class ParkingLocationAdmin(admin.ModelAdmin):
    save_as = True
    list_display = ("name", "type", "owner")


class RateScheduleAdmin(admin.ModelAdmin):
    list_display = ("name", )


admin.site.register(Rate, RateAdmin)
admin.site.register(ParkingLocation, ParkingLocationAdmin)
admin.site.register(RateSchedule, RateScheduleAdmin)