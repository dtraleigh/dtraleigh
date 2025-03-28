from django.contrib import admin
from parking.models import Rate, ParkingLocation, RateSchedule


class RateAdmin(admin.ModelAdmin):
    save_as = True
    list_display = ("day_of_week", "is_free", "all_day", "rate",
                    "start_time", "end_time", "date_created", "rate_schedule")


class ParkingLocationAdmin(admin.ModelAdmin):
    save_as = True
    list_display = ("name", "type", "cost", "owner", "rate_schedule", "is_enabled", "gmaps_params_encoded")


class RateScheduleAdmin(admin.ModelAdmin):
    list_display = ("name", )


admin.site.register(Rate, RateAdmin)
admin.site.register(ParkingLocation, ParkingLocationAdmin)
admin.site.register(RateSchedule, RateScheduleAdmin)