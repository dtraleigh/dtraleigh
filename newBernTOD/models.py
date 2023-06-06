from django.db import models
from django.contrib.gis.db import models
from simple_history.models import HistoricalRecords


class Parcel(models.Model):
    property_address = models.CharField(max_length=400)
    pin = models.CharField(max_length=200)
    acres = models.CharField(max_length=200)
    owner = models.CharField(max_length=200)
    curr_zoning = models.CharField(max_length=200)
    prop_zoning = models.CharField(max_length=200)
    history = HistoricalRecords()
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    geom = models.PolygonField(srid=4326, null=True)

    def __str__(self):
        return f"{self.id} - Pin:{self.pin}"


class Overlay(models.Model):
    # An Overlay is a collection of Parcels
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    parcels = models.ManyToManyField("Parcel", default=None, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.id})"
