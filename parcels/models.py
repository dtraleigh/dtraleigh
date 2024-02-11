from django.contrib.gis.db import models
from simple_history.models import HistoricalRecords


class Parcel(models.Model):
    property_address = models.CharField(max_length=400, blank=True, null=True)
    objectid = models.IntegerField()
    pin = models.CharField(max_length=200)
    defunct_pin = models.BooleanField(default=False)
    acres = models.CharField(max_length=200, blank=True, null=True)
    owner = models.CharField(max_length=200, blank=True, null=True)
    curr_zoning = models.CharField(max_length=200, blank=True, null=True)
    prop_zoning = models.CharField(max_length=200, blank=True, null=True)
    history = HistoricalRecords()
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True, verbose_name="Date")
    is_active = models.BooleanField(default=False)
    geom = models.PolygonField(srid=4326, null=True)
    reid = models.CharField(max_length=20, blank=True, null=True)
    addr1 = models.CharField(max_length=100, blank=True, null=True)
    addr2 = models.CharField(max_length=100, blank=True, null=True)
    addr3 = models.CharField(max_length=100, blank=True, null=True)
    deed_acres = models.DecimalField(max_digits=11, decimal_places=6, blank=True, null=True)
    bldg_val = models.IntegerField(blank=True, null=True, verbose_name="Building Value")
    land_val = models.IntegerField(blank=True, null=True, verbose_name="Land Value")
    total_value_assd = models.IntegerField(blank=True, null=True)
    propdesc = models.CharField(max_length=250, blank=True, null=True)
    year_built = models.IntegerField(blank=True, null=True)
    totsalprice = models.DecimalField(max_digits=11, decimal_places=2, blank=True, null=True, verbose_name="Sale Price")
    sale_date = models.BigIntegerField(blank=True, null=True, verbose_name="Sale Date")
    type_and_use = models.CharField(max_length=100, blank=True, null=True)
    type_use_decode = models.CharField(max_length=100, blank=True, null=True)
    designstyl = models.CharField(max_length=100, blank=True, null=True)
    design_style_decode = models.CharField(max_length=100, blank=True, null=True)
    units = models.DecimalField(max_digits=11, decimal_places=2, blank=True, null=True)
    totstructs = models.IntegerField(blank=True, null=True, verbose_name="Total Structures")
    totunits = models.IntegerField(blank=True, null=True, verbose_name="Total Units")
    site = models.IntegerField(blank=True, null=True)
    city = models.CharField(max_length=8, blank=True, null=True)
    city_decode = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        ordering = ["modified_date"]

    def __str__(self):
        return f"{self.id} - Pin:{self.pin}, objectid: {self.objectid}"


class Snapshot(models.Model):
    name = models.CharField(max_length=200)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Snapshot {self.name} (id:{self.id})"


class ParcelHistorical(models.Model):
    data_geojson = models.JSONField()
    snapshot = models.ForeignKey(Snapshot, on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"ParcelHistorical (id:{self.id})"


class RaleighSubsection(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True, verbose_name="Date")
    geom = models.GeometryField(srid=4326)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"RaleighSubsection (id:{self.id})"
