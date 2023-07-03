import datetime

from django.contrib import admin
from django.contrib.gis import admin

from develop.models import *

from simple_history.admin import SimpleHistoryAdmin
from django.contrib.admin import ModelAdmin, SimpleListFilter


class ControlAdmin(admin.ModelAdmin):
    list_display = ("scrape", "scan", "notify")


class SubscriberAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "comments", "role", "send_emails", "is_bot", "topic_id")


class DevelopmentPlansAdmin(admin.OSMGeoAdmin):
    list_display = ("objectid", "plan_type", "submitted", "status", "major_stre", "geom",
                    "plan_name", "plan_numbe", "planurl", "modified_date", "created_date")
    history_list_display = ["status"]


class SiteReviewCaseAdmin(SimpleHistoryAdmin):
    list_display = ("case_number", "project_name", "status", "modified_date",
                    "created_date")
    history_list_display = ["status"]


class ZoningAdmin(SimpleHistoryAdmin):
    list_display = ("zpyear", "zpnum", "location", "status", "location", "short_location_url",
                    "short_plan_url", "modified_date", "created_date")


class AADAdmin(SimpleHistoryAdmin):
    list_display = ("case_number", "project_name", "status", "modified_date",
                    "created_date")
    history_list_display = ["status"]


class TCAdmin(SimpleHistoryAdmin):
    list_display = ("case_number", "project_name", "status", "modified_date", "created_date")
    history_list_display = ["status"]


class NMAdmin(SimpleHistoryAdmin):
    list_display = ("meeting_datetime_details", "rezoning_site_address", "created_date", "modified_date")


class DACAdmin(SimpleHistoryAdmin):
    list_display = ("case_number", "project_name", "status", "modified_date",
                    "created_date")
    history_list_display = ["status"]


admin.site.register(Control, ControlAdmin)
admin.site.register(SiteReviewCase, SiteReviewCaseAdmin)
admin.site.register(Subscriber, SubscriberAdmin)
admin.site.register(Zoning, ZoningAdmin)
admin.site.register(AdministrativeAlternate, AADAdmin)
admin.site.register(TextChangeCase, TCAdmin)
admin.site.register(WakeCorporate, admin.OSMGeoAdmin)
admin.site.register(TrackArea, admin.OSMGeoAdmin)
admin.site.register(DevelopmentPlan, DevelopmentPlansAdmin)
admin.site.register(NeighborhoodMeeting, NMAdmin)
admin.site.register(DesignAlternateCase, DACAdmin)
