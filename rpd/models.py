from datetime import datetime

from django.db import models
from django.contrib.gis.db import models


class TrackArea(models.Model):
    objectid = models.IntegerField()
    short_name = models.CharField(max_length=8)
    long_name = models.CharField(max_length=50)
    geom = models.MultiPolygonField(srid=4326)

    def __str__(self):
        return self.long_name


trackarea_mapping = {
    "objectid": "OBJECTID",
    "short_name": "SHORT_NAME",
    "long_name": "LONG_NAME",
    "geom": "MULTIPOLYGON",
}


# This is an auto-generated Django model module created by ogrinspect.
class RaleighPoliceDistrict(models.Model):
    objectid = models.IntegerField()
    district = models.CharField(max_length=3)
    shape_are = models.FloatField()
    shape_len = models.FloatField()
    zoneid = models.IntegerField()
    geom = models.MultiPolygonField(srid=4326)


# Auto-generated `LayerMapping` dictionary for RaleighPoliceDistrict model
raleigh_police_districts_mapping = {
    "objectid": "OBJECTID",
    "district": "DISTRICT",
    "shape__are": "Shape_Are",
    "shape__len": "Shape_Len",
    "zoneid": "ZONEID",
    "geom": "MULTIPOLYGON",
}


class Incident(models.Model):
    objectid = models.IntegerField()
    globalid = models.CharField(max_length=100, blank=True, null=True)
    crime_category = models.CharField(max_length=100, blank=True, null=True)
    crime_description = models.CharField(max_length=100, blank=True, null=True)
    crime_type = models.CharField(max_length=100, blank=True, null=True)
    reported_block_address = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    reported_date = models.BigIntegerField(blank=True, null=True)
    reported_year = models.IntegerField(blank=True, null=True)
    reported_month = models.IntegerField(blank=True, null=True)
    reported_day = models.IntegerField(blank=True, null=True)
    reported_hour = models.IntegerField(blank=True, null=True)
    reported_dayofwk = models.CharField(max_length=20, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    geom = models.PointField(blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    is_glenwood_south = models.BooleanField(default=False)

    def __str__(self):
        return f"Incident {self.objectid}"

    incident_mapping = {
        "objectid": "OBJECTID",
        "globalid": "GlobalID",
        "crime_category": "crime_category",
        "crime_description": "crime_description",
        "crime_type": "crime_type",
        "reported_block_address": "reported_block_address",
        "district": "district",
        "reported_date": "reported_date",
        "reported_year": "reported_year",
        "reported_month": "reported_month",
        "reported_day": "reported_day",
        "reported_hour": "reported_hour",
        "reported_dayofwk": "reported_dayofwk",
        "latitude": "latitude",
        "longitude": "longitude"
    }

    def get_datetime_object(self):
        return datetime(self.reported_year, self.reported_month, self.reported_day)

    def is_year_to_date(self):
        # Return true if this incident is between Jan 1 and less than today, regardless of year
        todays_month = datetime.today().month
        todays_day = datetime.today().day

        if self.reported_month == todays_month and self.reported_day < todays_day:
            return True
        elif self.reported_month < todays_month:
            return True
        else:
            return False
