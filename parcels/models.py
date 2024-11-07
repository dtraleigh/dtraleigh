import json

from django.contrib.gis.db import models
from django.contrib.gis.geos import GEOSGeometry
from simple_history.models import HistoricalRecords

from parcels.parcel_archive.functions import identify_coordinate_system_from_parcel, convert_geometry_to_epsg4326


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

    def get_geosgeom_object(self):
        if self.data_geojson["geometry"] and identify_coordinate_system_from_parcel(self) == "epsg:4326":
            return GEOSGeometry(str(self.data_geojson["geometry"]))
        elif self.data_geojson["geometry"] and identify_coordinate_system_from_parcel(self) == "epsg:2264":
            converted_geometry = str(convert_geometry_to_epsg4326(self.data_geojson["geometry"]))
            return GEOSGeometry(converted_geometry)
        else:
            return None

    def get_total_value(self):
        keys_to_check = ["TOTAL_VALU", "TOTVALASSD"]
        for key in keys_to_check:
            try:
                return self.data_geojson["properties"][key]
            except KeyError:
                continue
        raise KeyError(f"None of the keys {keys_to_check} were found in the data. {self.data_geojson}")

    def get_propdesc(self):
        keys_to_check = ["PROPDESC"]
        for key in keys_to_check:
            try:
                return self.data_geojson["properties"][key]
            except KeyError:
                continue
        raise KeyError(f"None of the keys {keys_to_check} were found in the data. {self.data_geojson}")

    def get_first_coord(self):
        geom = GEOSGeometry(str(self.data_geojson["geometry"]))

        first_coord = [35.88959578462791, -78.73211042127825]

        if geom.geom_type == "Polygon":
            first_coord = self.data_geojson["geometry"]["coordinates"][0][0]

        elif geom.geom_type == "MultiPolygon":
            first_coord = self.data_geojson["geometry"]["coordinates"][0][0][0]

        return first_coord


class RaleighSubsection(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True, verbose_name="Date")
    geom = models.GeometryField(srid=4326)
    sections = models.ManyToManyField(ParcelHistorical)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"RaleighSubsection (id:{self.id})"
