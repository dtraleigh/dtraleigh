from django.db import models
from django.contrib.gis.db import models
from simple_history.models import HistoricalRecords


class Control(models.Model):
    scrape = models.BooleanField(default=True)
    scan = models.BooleanField(default=True)
    notify = models.BooleanField(default=True)


class WakeCorporate(models.Model):
    objectid = models.IntegerField()
    short_name = models.CharField(max_length=3, null=True)
    long_name = models.CharField(max_length=13, null=True)
    ordinance_field = models.CharField(max_length=18, null=True)
    effective_field = models.DateField(null=True)
    shapearea = models.FloatField(null=True)
    shapelen = models.FloatField(null=True)
    geom = models.MultiPolygonField(srid=4326, null=True)


# Auto-generated `LayerMapping` dictionary for WakeCorporate model
wakecorporate_mapping = {
    'objectid': 'OBJECTID',
    'short_name': 'SHORT_NAME',
    'long_name': 'LONG_NAME',
    'ordinance_field': 'ORDINANCE_',
    'effective_field': 'EFFECTIVE_',
    'shapearea': 'SHAPEAREA',
    'shapelen': 'SHAPELEN',
    'geom': 'MULTIPOLYGON',
}


class TrackArea(models.Model):
    objectid = models.IntegerField()
    short_name = models.CharField(max_length=3)
    long_name = models.CharField(max_length=13)
    geom = models.MultiPolygonField(srid=4326)

    def __str__(self):
        return self.long_name


trackarea_mapping = {
    "objectid": "OBJECTID",
    "short_name": "SHORT_NAME",
    "long_name": "LONG_NAME",
    "geom": "MULTIPOLYGON",
}


class Subscriber(models.Model):
    date_created = models.DateTimeField(auto_now_add=True, verbose_name="Date Subscribed")
    name = models.CharField(max_length=254)
    email = models.EmailField(unique=True)
    send_emails = models.BooleanField(default=True, verbose_name="Email and post to Discourse")
    comments = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(max_length=100, blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    is_bot = models.BooleanField(default=False)
    topic_id = models.IntegerField(blank=True, null=True, verbose_name="Topic ID")
    api_key = models.CharField(max_length=254, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.email})"


class DevelopmentPlan(models.Model):
    """Mainly Zoning and Admin Site Reviews. This could replace Zoning and SiteReviewCase models"""
    objectid = models.IntegerField()
    devplan_id = models.IntegerField(blank=True, null=True)  # deprecated, fields no longer in the API as of Jan 2024
    submitted = models.DateField(blank=True, null=True)
    submitted_field = models.IntegerField(blank=True, null=True)
    approved = models.DateField(blank=True, null=True)
    daystoappr = models.IntegerField(blank=True, null=True)  # deprecated, fields no longer in the API as of Jan 2024
    plan_type = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=30, blank=True, null=True)
    appealperi = models.DateField(blank=True, null=True)
    updated = models.DateField(blank=True, null=True)
    sunset_dat = models.DateField(blank=True, null=True)
    acreage = models.FloatField(blank=True, null=True)
    major_street = models.CharField(max_length=100, blank=True, null=True)
    cac = models.CharField(max_length=30, blank=True, null=True)  # deprecated, fields no longer in the API as of Jan 2024
    engineer = models.CharField(max_length=100, blank=True, null=True)  # deprecated, fields no longer in the API as of Jan 2024
    engineer_p = models.CharField(max_length=20, blank=True, null=True)  # deprecated, fields no longer in the API as of Jan 2024
    developer = models.CharField(max_length=100, blank=True, null=True)
    developer_field = models.CharField(max_length=20, blank=True, null=True)  # deprecated, fields no longer in the API as of Jan 2024
    plan_name = models.CharField(max_length=200, blank=True, null=True)
    planurl = models.CharField(max_length=255, blank=True, null=True)  # deprecated, fields no longer in the API as of Jan 2024
    planurl_ap = models.CharField(max_length=255, blank=True, null=True)  # deprecated, fields no longer in the API as of Jan 2024
    planner = models.CharField(max_length=50, blank=True, null=True)  # deprecated, fields no longer in the API as of Jan 2024
    lots_req = models.IntegerField(blank=True, null=True)
    lots_rec = models.IntegerField(blank=True, null=True)  # deprecated, fields no longer in the API as of Jan 2024
    lots_apprv = models.IntegerField(blank=True, null=True)
    sq_ft_req = models.IntegerField(blank=True, null=True)
    units_appr = models.IntegerField(blank=True, null=True)
    units_req = models.IntegerField(blank=True, null=True)
    zoning = models.CharField(max_length=50, blank=True, null=True)
    plan_numbe = models.CharField(max_length=20, blank=True, null=True)
    creationda = models.DateField(blank=True, null=True)  # deprecated, fields no longer in the API as of Jan 2024
    creator = models.CharField(max_length=12, blank=True, null=True)  # deprecated, fields no longer in the API as of Jan 2024
    editdate = models.DateField(blank=True, null=True)  # deprecated, fields no longer in the API as of Jan 2024
    editor = models.CharField(max_length=12, blank=True, null=True)  # deprecated, fields no longer in the API as of Jan 2024
    global_id = models.CharField(max_length=38, blank=True, null=True)
    missing_middle = models.CharField(max_length=10, blank=True, null=True)
    geom = models.PointField(blank=True, null=True)
    history = HistoricalRecords()
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Development Plan"

    def __str__(self):
        return f"Dev - {self.plan_name} - {self.devplan_id} ({self.submitted})"

    # Model field: JSON field
    developmentplan_mapping = {
        "objectid": "OBJECTID",
        "devplan_id": "devplan_id",
        "submitted": "submitted",
        "submitted_field": "submitted_yr",
        "approved": "approved",
        "daystoappr": "daystoapprove",
        "plan_type": "plan_type",
        "status": "status",
        "appealperi": "appealperiodends",
        "updated": "updated",
        "sunset_dat": "sunset_date",
        "acreage": "acreage",
        "major_stre": "major_street",
        "cac": "cac",
        "engineer": "engineer",
        "engineer_p": "engineer_phone",
        "developer": "developer",
        "developer_field": "developer_phone",
        "plan_name": "plan_name",
        "planurl": "planurl",
        "planurl_ap": "planurl_approved",
        "planner": "planner",
        "lots_req": "lots_req",
        "lots_rec": "lots_rec",
        "lots_apprv": "lots_apprv",
        "sq_ft_req": "sq_ft_req",
        "units_appr": "units_appr",
        "units_req": "units_req",
        "zoning": "zoning",
        "plan_numbe": "plan_number",
        "creationda": "CreationDate",
        "creator": "Creator",
        "editdate": "EditDate",
        "editor": "Editor",
        "geom": "POINT",
    }


class SiteReviewCase(models.Model):
    """A Site Review Case is an item on the Development Activity page - Site Review Cases (SR) section"""
    case_number = models.CharField(blank=True, max_length=100, null=True, verbose_name="Case Number")
    case_url = models.TextField(blank=True, null=True, verbose_name="Plan URL")
    project_name = models.CharField(blank=True, max_length=300, null=True, verbose_name="Plan Name")
    status = models.CharField(blank=True, max_length=100, null=True, verbose_name="Status")
    history = HistoricalRecords()
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site Review Case"

    def __str__(self):
        return f"SR - {self.case_number} - {self.project_name}"


class Zoning(models.Model):
    zpyear = models.SmallIntegerField(blank=True, null=True, verbose_name="Year Submitted")
    zpnum = models.SmallIntegerField(blank=True, null=True, verbose_name="Zoning Number")
    location = models.CharField(blank=True, max_length=300, null=True, verbose_name="Location")
    location_url = models.TextField(blank=True, null=True, verbose_name="Location URL")
    status = models.CharField(blank=True, max_length=300, null=True, verbose_name="Status")  # Web scrape field
    plan_url = models.TextField(blank=True, null=True, verbose_name="Plan URL")
    received_by = models.CharField(blank=True, max_length=300, null=True, verbose_name="Received By")
    history = HistoricalRecords()
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Zoning Request"

    def __str__(self):
        return f"Zone - {self.zpnum} ({self.zpyear})"

    @property
    def short_location_url(self):
        if self.location_url:
            return self.location_url if len(self.location_url) < 35 else (self.location_url[:33] + "..")

    @property
    def short_plan_url(self):
        if self.plan_url:
            return self.plan_url if len(self.plan_url) < 35 else (self.plan_url[:33] + "..")


class AdministrativeAlternate(models.Model):
    """An Administrative Alternate is an item on the Development Activity page -
    Administrative Alternate Requests (AAD) section"""
    case_number = models.CharField(blank=True, max_length=300, null=True, verbose_name="Case Number")
    case_url = models.TextField(blank=True, null=True, verbose_name="Plan URL")
    project_name = models.CharField(blank=True, max_length=300, null=True, verbose_name="Plan Name")
    status = models.CharField(blank=True, max_length=300, null=True, verbose_name="Status")
    history = HistoricalRecords()
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Administrative Alternate Request"

    def __str__(self):
        return f"AAR - {self.case_number} - {self.project_name}"


class TextChangeCase(models.Model):
    """A text change case is an item on the Development Activity page - Text Change Cases (TC) section"""
    case_number = models.CharField(blank=True, max_length=100, null=True, verbose_name="Case Number")
    case_url = models.TextField(blank=True, null=True, verbose_name="Plan URL")
    project_name = models.CharField(blank=True, max_length=300, null=True, verbose_name="Plan Name")
    description = models.CharField(blank=True, max_length=1000, null=True)
    status = models.CharField(blank=True, max_length=100, null=True, verbose_name="Status")
    history = HistoricalRecords()
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Text Change Case"

    def __str__(self):
        return f"TCC - {self.case_number} - {self.project_name}"


class NeighborhoodMeeting(models.Model):
    meeting_datetime_details = models.CharField(blank=True, max_length=300, null=True, verbose_name="Meeting Date/Time")
    meeting_location = models.CharField(blank=True, max_length=300, null=True, verbose_name="Meeting Location")
    rezoning_site_address = models.CharField(blank=True, max_length=300, null=True,
                                             verbose_name="Rezoning Site Address")
    rezoning_site_address_url = models.TextField(blank=True, null=True, verbose_name="Rezoning Site Address URL")
    rezoning_request = models.CharField(blank=True, max_length=300, null=True, verbose_name="Rezoning Request")
    rezoning_request_url = models.TextField(blank=True, null=True, verbose_name="Rezoning Request URL")
    history = HistoricalRecords()
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Neighborhood Meeting"

    def __str__(self):
        return f"Meeting - {self.meeting_datetime_details} - {self.rezoning_site_address}"

    def clean_meeting_details(self):
        self.meeting_datetime_details = self.meeting_datetime_details.replace("\n", "")
        self.meeting_datetime_details = self.meeting_datetime_details.replace("\t", "")
        super().save()


class DesignAlternateCase(models.Model):
    case_number = models.CharField(blank=True, max_length=100, null=True, verbose_name="Case Number")
    case_url = models.TextField(blank=True, null=True, verbose_name="Plan URL")
    project_name = models.CharField(blank=True, max_length=300, null=True, verbose_name="Plan Name")
    status = models.CharField(blank=True, max_length=100, null=True, verbose_name="Status")
    history = HistoricalRecords()
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Design Alternate Case"

    def __str__(self):
        return f"DA case = {self.case_number} - {self.project_name}"

# This is an auto-generated Django model module created by ogrinspect.
class WakeRacialCovenant(models.Model):
    docid = models.CharField(max_length=12)
    rownum = models.CharField(max_length=20)
    url = models.CharField(max_length=254, null=True, blank=True)
    bookpage = models.CharField(max_length=254, null=True, blank=True)
    grantor = models.CharField(max_length=254, null=True, blank=True)
    grantee = models.CharField(max_length=254, null=True, blank=True)
    doctypedes = models.CharField(max_length=254, null=True, blank=True)
    doctypeid = models.CharField(max_length=254, null=True, blank=True)
    recorddate = models.DateField()
    execdate = models.DateField()
    propertyde = models.CharField(max_length=254, null=True, blank=True)
    bm = models.CharField(max_length=254, null=True, blank=True)
    lots = models.CharField(max_length=254, null=True, blank=True)
    notes = models.CharField(max_length=254, null=True, blank=True)
    mapreview = models.CharField(max_length=254, null=True, blank=True)
    bestmap = models.CharField(max_length=254, null=True, blank=True)
    geom = models.MultiPolygonField(srid=2264)
