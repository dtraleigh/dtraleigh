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
    reid = models.CharField(max_length=20, blank=True, null=True)
    addr1 = models.CharField(max_length=100, blank=True, null=True)
    addr2 = models.CharField(max_length=100, blank=True, null=True)
    addr3 = models.CharField(max_length=100, blank=True, null=True)
    deed_acres = models.DecimalField(max_digits=11, decimal_places=6, blank=True, null=True)
    bldg_val = models.IntegerField(blank=True, null=True)
    land_val = models.IntegerField(blank=True, null=True)
    total_value_assd = models.IntegerField(blank=True, null=True)
    propdesc = models.CharField(max_length=250, blank=True, null=True)
    year_built = models.IntegerField(blank=True, null=True)
    totsalprice = models.DecimalField(max_digits=11, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"{self.id} - Pin:{self.pin}"


class Overlay(models.Model):
    # An Overlay is a collection of Parcels
    OLAY_NAME = models.CharField(max_length=250, blank=True, null=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    OVERLAY = models.CharField(max_length=250, blank=True, null=True)
    OBJECTID = models.IntegerField(blank=True, null=True)
    ZONE_CASE = models.CharField(max_length=250, blank=True, null=True)
    ORDINANCE = models.CharField(max_length=250, blank=True, null=True)
    EFF_DATE = models.BigIntegerField(blank=True, null=True)
    geom = models.PolygonField(srid=4326, null=True, blank=True)
    parcels = models.ManyToManyField("Parcel", default=None, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.OLAY_NAME} ({self.id})"

    def get_num_parcels_in_tod(self):
        new_bern_tod = Overlay.objects.prefetch_related("parcels").get(name="New Bern TOD")

        num_parcels_in_tod = 0
        for parcel in [p for p in self.parcels.all()]:
            if parcel in [x for x in new_bern_tod.parcels.all()]:
                num_parcels_in_tod += 1

        return num_parcels_in_tod

    def get_num_parcels_not_in_tod(self):
        new_bern_tod = Overlay.objects.prefetch_related("parcels").get(name="New Bern TOD")

        num_parcels_in_tod = 0
        for parcel in [p for p in self.parcels.all()]:
            if parcel not in [x for x in new_bern_tod.parcels.all()]:
                num_parcels_in_tod += 1

        return num_parcels_in_tod

    def get_num_parcels(self):
        return len(self.parcels.all())
