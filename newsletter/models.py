import uuid
from django.db import models


class Subscriber(models.Model):
    STATUS_UNCONFIRMED = "unconfirmed"
    STATUS_CONFIRMED = "confirmed"
    STATUS_UNSUBSCRIBED = "unsubscribed"
    STATUS_BOUNCED = "bounced"

    STATUS_CHOICES = [
        (STATUS_UNCONFIRMED, "Unconfirmed"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_UNSUBSCRIBED, "Unsubscribed"),
        (STATUS_BOUNCED, "Bounced"),
    ]

    email = models.EmailField(unique=True, db_index=True)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_UNCONFIRMED)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    bounced_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.email} ({self.status})"

    class Meta:
        ordering = ["-created_at"]


class SentPost(models.Model):
    guid = models.CharField(max_length=500, unique=True)
    title = models.CharField(max_length=500)
    sent_at = models.DateTimeField(auto_now_add=True)
    recipient_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.title} ({self.sent_at.strftime('%Y-%m-%d')})"

    class Meta:
        ordering = ["-sent_at"]


class SendLog(models.Model):
    EVENT_NEWSLETTER_SENT = "newsletter_sent"
    EVENT_CONFIRMATION_SENT = "confirmation_sent"
    EVENT_BOUNCE = "bounce"
    EVENT_COMPLAINT = "complaint"
    EVENT_ERROR = "error"

    EVENT_CHOICES = [
        (EVENT_NEWSLETTER_SENT, "Newsletter Sent"),
        (EVENT_CONFIRMATION_SENT, "Confirmation Sent"),
        (EVENT_BOUNCE, "Bounce"),
        (EVENT_COMPLAINT, "Complaint"),
        (EVENT_ERROR, "Error"),
    ]

    sent_post = models.ForeignKey(SentPost, on_delete=models.SET_NULL, null=True, blank=True)
    subscriber = models.ForeignKey("Subscriber", on_delete=models.SET_NULL, null=True, blank=True)
    event_type = models.CharField(max_length=30, choices=EVENT_CHOICES)
    detail = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event_type} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ["-created_at"]
