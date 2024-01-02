from django.contrib.gis.db import models
from simple_history.models import HistoricalRecords

arterial_roads = ["NEW BERN AVE", "RALEIGH BLVD", "EDENTON ST"]


class NewBernParcel(models.Model):
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
    modified_date = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=False)
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


class Overlay(models.Model):
    olay_name = models.CharField(max_length=250, blank=True, null=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    overlay = models.CharField(max_length=250, blank=True, null=True)
    OBJECTID = models.IntegerField(blank=True, null=True)
    ZONE_CASE = models.CharField(max_length=250, blank=True, null=True)
    ORDINANCE = models.CharField(max_length=250, blank=True, null=True)
    EFF_DATE = models.BigIntegerField(blank=True, null=True)
    geom = models.PolygonField(srid=4326, null=True, blank=True)
    parcels = models.ManyToManyField("NewBernParcel", default=None, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.olay_name} {self.overlay} ({self.id})"

    def get_num_parcels_in_tod(self):
        new_bern_tod = Overlay.objects.prefetch_related("parcels").get(name="New Bern TOD")

        num_parcels_in_tod = 0
        for parcel in [p for p in self.parcels.all()]:
            if parcel in [x for x in new_bern_tod.parcels.all()]:
                num_parcels_in_tod += 1

        return num_parcels_in_tod

    def get_num_parcels_in_tod_and_arterial(self):
        new_bern_tod = Overlay.objects.prefetch_related("parcels").get(name="New Bern TOD")

        num_parcels_in_tod_and_arterial = 0
        for parcel in [p for p in self.parcels.all()]:
            if parcel in [x for x in new_bern_tod.parcels.all()]:
                for road in arterial_roads:
                    if road in parcel.addr1:
                        num_parcels_in_tod_and_arterial += 1

        return num_parcels_in_tod_and_arterial

    def get_num_parcels_not_in_tod(self):
        new_bern_tod = Overlay.objects.prefetch_related("parcels").get(name="New Bern TOD")

        num_parcels_in_tod = 0
        for parcel in [p for p in self.parcels.all()]:
            if parcel not in [x for x in new_bern_tod.parcels.all()]:
                num_parcels_in_tod += 1

        return num_parcels_in_tod

    def get_num_parcels(self):
        return len(self.parcels.all())


# This is an auto-generated Django model module created by ogrinspect.
class NCOD(models.Model):
    objectid = models.IntegerField()
    overlay = models.CharField(max_length=4)
    olay_decod = models.CharField(max_length=42)
    olay_name = models.CharField(max_length=25)
    zone_case = models.CharField(max_length=9)
    ordinance = models.CharField(max_length=8)
    eff_date = models.DateField()
    overlay_ty = models.CharField(max_length=28)
    shape_leng = models.FloatField()
    shape_area = models.FloatField()
    geom = models.MultiPolygonField(srid=4326)
    parcels = models.ManyToManyField("NewBernParcel", default=None, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.olay_name} {self.overlay} ({self.id})"

    def get_num_parcels_in_tod(self):
        new_bern_tod = Overlay.objects.prefetch_related("parcels").get(name="New Bern TOD")

        num_parcels_in_tod = 0
        for parcel in [p for p in self.parcels.all()]:
            if parcel in [x for x in new_bern_tod.parcels.all()]:
                num_parcels_in_tod += 1

        return num_parcels_in_tod

    def get_num_parcels_in_tod_and_arterial(self):
        new_bern_tod = Overlay.objects.prefetch_related("parcels").get(name="New Bern TOD")

        num_parcels_in_tod_and_arterial = 0
        for parcel in [p for p in self.parcels.all()]:
            if parcel in [x for x in new_bern_tod.parcels.all()]:
                for road in arterial_roads:
                    if road in parcel.addr1:
                        num_parcels_in_tod_and_arterial += 1

        return num_parcels_in_tod_and_arterial

    def get_num_parcels_not_in_tod(self):
        new_bern_tod = Overlay.objects.prefetch_related("parcels").get(name="New Bern TOD")

        num_parcels_in_tod = 0
        for parcel in [p for p in self.parcels.all()]:
            if parcel not in [x for x in new_bern_tod.parcels.all()]:
                num_parcels_in_tod += 1

        return num_parcels_in_tod

    def get_num_parcels(self):
        return len(self.parcels.all())


# This is an auto-generated Django model module created by ogrinspect.
class HOD(models.Model):
    objectid = models.IntegerField()
    overlay = models.CharField(max_length=5)
    olay_decod = models.CharField(max_length=36)
    olay_name = models.CharField(max_length=17)
    zone_case = models.CharField(max_length=10)
    ordinance = models.CharField(max_length=8)
    eff_date = models.DateField()
    overlay_ty = models.CharField(max_length=28)
    shape_leng = models.FloatField()
    shape_area = models.FloatField()
    geom = models.MultiPolygonField(srid=4326)
    parcels = models.ManyToManyField("NewBernParcel", default=None, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.olay_name} {self.overlay} ({self.id})"

    def get_num_parcels_in_tod(self):
        new_bern_tod = Overlay.objects.prefetch_related("parcels").get(name="New Bern TOD")

        num_parcels_in_tod = 0
        for parcel in [p for p in self.parcels.all()]:
            if parcel in [x for x in new_bern_tod.parcels.all()]:
                num_parcels_in_tod += 1

        return num_parcels_in_tod

    def get_num_parcels_in_tod_and_arterial(self):
        new_bern_tod = Overlay.objects.prefetch_related("parcels").get(name="New Bern TOD")

        num_parcels_in_tod_and_arterial = 0
        for parcel in [p for p in self.parcels.all()]:
            if parcel in [x for x in new_bern_tod.parcels.all()]:
                for road in arterial_roads:
                    if road in parcel.addr1:
                        num_parcels_in_tod_and_arterial += 1

        return num_parcels_in_tod_and_arterial

    def get_num_parcels_not_in_tod(self):
        new_bern_tod = Overlay.objects.prefetch_related("parcels").get(name="New Bern TOD")

        num_parcels_in_tod = 0
        for parcel in [p for p in self.parcels.all()]:
            if parcel not in [x for x in new_bern_tod.parcels.all()]:
                num_parcels_in_tod += 1

        return num_parcels_in_tod

    def get_num_parcels(self):
        return len(self.parcels.all())
