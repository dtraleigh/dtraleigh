from django.contrib.gis.db import models


class Building(models.Model):
    objectid = models.IntegerField()
    PIN_NUM = models.CharField(max_length=20, null=True)
    ADDR1 = models.CharField(max_length=200, null=True)
    PROPDESC = models.CharField(max_length=300, null=True)
    SITE_ADDRESS = models.CharField(max_length=200, null=True)
    YEAR_BUILT = models.IntegerField(null=True)
    TYPE_USE_DECODE = models.CharField(max_length=50, null=True)
    CITY = models.CharField(max_length=50)
    LAND_VAL = models.IntegerField(null=True)
    DEED_ACRES = models.DecimalField(max_digits=11, decimal_places=6, null=True)
    LAND_VAL_per_DEED_ACRES = models.DecimalField(max_digits=19, decimal_places=9, null=True)
    geom = models.PolygonField(srid=4326, null=True)

    def __str__(self):
        return f"{self.objectid} - Pin:{self.PIN_NUM} ({self.YEAR_BUILT})"


class Decade(models.Model):
    decade_name = models.CharField(max_length=20, null=True)
    start_year = models.IntegerField()
    end_year = models.IntegerField()
    output_geojson_reduced = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ["start_year"]

    def __str__(self):
        return f"{self.decade_name}"


class Border(models.Model):
    muni_name = models.CharField(max_length=50)
    created_date = models.DateTimeField(auto_now_add=True)
    border_geojson = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.muni_name} border"


class CustomMap(models.Model):
    map_name = models.CharField(max_length=200)
    created_date = models.DateTimeField(auto_now_add=True)
    output_geojson = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.map_name}"
