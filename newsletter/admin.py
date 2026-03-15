from django.contrib import admin

from .models import Subscriber, SentPost, SendLog


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "status", "created_at", "confirmed_at")
    list_filter = ("status",)
    search_fields = ("email",)
    readonly_fields = ("token", "created_at", "confirmed_at", "unsubscribed_at", "bounced_at")


@admin.register(SentPost)
class SentPostAdmin(admin.ModelAdmin):
    list_display = ("title", "sent_at", "recipient_count")
    readonly_fields = ("sent_at",)


@admin.register(SendLog)
class SendLogAdmin(admin.ModelAdmin):
    list_display = ("event_type", "subscriber", "sent_post", "created_at")
    list_filter = ("event_type",)
    readonly_fields = ("created_at",)
