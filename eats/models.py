from django.db import models
import datetime


class District(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    link = models.URLField(blank=True)
    photo = models.URLField(blank=True)
    district_map = models.URLField(blank=True)

    def __str__(self):
        return self.name


class Business(models.Model):
    date_added = models.DateTimeField(auto_now_add=True, verbose_name="Date added.")
    name = models.CharField(max_length=200)
    district = models.ForeignKey("District", on_delete=models.SET_NULL, null=True)
    link = models.URLField(max_length=500)
    description = models.TextField(default=None, blank=True, null=True)
    latitude = models.IntegerField(default=None, blank=True, null=True, verbose_name="Latitude")
    longitude = models.IntegerField(default=None, blank=True, null=True, verbose_name="Longitude")
    has_outdoor_seating = models.BooleanField(verbose_name="Outdoor Seating?")
    is_temp_closed = models.BooleanField(verbose_name="Temporarily closed?")
    is_eats = models.BooleanField(verbose_name="Eats")
    is_drinks = models.BooleanField(verbose_name="Drinks")
    is_coffee = models.BooleanField(verbose_name="Coffees")
    is_food_hall = models.BooleanField(verbose_name="Food Hall?", default=False)
    not_local = models.BooleanField(verbose_name="Not local?")
    open_date = models.DateField()
    close_date = models.DateField(null=True, blank=True, verbose_name="First closed date")

    @property
    def is_new_biz(self):
        """New implies the business opened less than 90 days ago"""
        today = datetime.date.today()
        if today < self.open_date + datetime.timedelta(days=90) and today >= self.open_date:
            return True
        return False

    @property
    def is_open(self):
        """Open implies the business is not past its close date and today is past or equal to the open date"""
        today = datetime.date.today()
        if today >= self.open_date and (self.close_date > today or self.close_date is None):
            return True
        return False

    @property
    def is_coming_soon(self):
        """coming soon implies the business has not opened yet but we have an opening date"""
        today = datetime.date.today()
        if today < self.open_date and self.close_date is None:
            return True
        return False

    @property
    def get_cname(self):
        class_name = "business"
        return class_name

    class Meta:
        verbose_name = "Business"
        verbose_name_plural = "Businesses"

    def __str__(self):
        return self.name


class Vendor(models.Model):
    """vendors are primarily for stalls inside a food hall, which is a business object itself."""
    date_added = models.DateTimeField(auto_now_add=True, verbose_name="Date added.")
    food_hall = models.ForeignKey("Business", on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200)
    link = models.URLField(max_length=500)
    description = models.TextField(default=None, blank=True, null=True)
    is_temp_closed = models.BooleanField(verbose_name="Temporarily closed?")
    not_local = models.BooleanField(verbose_name="Not local?")
    open_date = models.DateField()
    close_date = models.DateField(null=True, blank=True, verbose_name="First closed date")

    @property
    def is_new_biz(self):
        """New implies the business opened less than 90 days ago"""
        today = datetime.date.today()
        if today < self.open_date + datetime.timedelta(days=90) and today >= self.open_date:
            return True
        return False

    @property
    def is_open(self):
        """Open implies the business is not past its close date and today is past or equal to the open date"""
        today = datetime.date.today()
        if today >= self.open_date and (self.close_date > today or self.close_date is None):
            return True
        return False

    @property
    def is_coming_soon(self):
        """coming soon implies the business has not opened yet but we have an opening date"""
        today = datetime.date.today()
        if today < self.open_date and self.close_date is None:
            return True
        return False

    @property
    def get_cname(self):
        class_name = "vendor"
        return class_name

    class Meta:
        verbose_name = "Vendor"
        verbose_name_plural = "Vendors"

    def __str__(self):
        return self.name


class Snapshot(models.Model):
    date = models.DateField(auto_now_add=True)
    local_business_count = models.IntegerField()
    not_local_business_count = models.IntegerField()
    businesses = models.ManyToManyField(Business)

    def __str__(self):
        return f"Snapshot on {self.date}"


class ReferenceLink(models.Model):
    url_link = models.URLField(max_length=500, unique=True)
    description = models.CharField(max_length=500, default=None, blank=True, null=True)
    headline = models.CharField(max_length=500)
    date_published = models.DateField(default=None, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Reference Link"
        verbose_name_plural = "Reference Links"
        ordering = ["-date_created"]

    def __str__(self):
        return self.headline


class Tip(models.Model):
    date = models.DateField(auto_now_add=True, verbose_name="Date added.")
    name = models.CharField(max_length=200)
    district = models.ForeignKey("District", on_delete=models.SET_NULL, blank=True, null=True)
    food_hall = models.ForeignKey("Business", on_delete=models.SET_NULL, blank=True, null=True)
    link = models.URLField(max_length=500, default=None, blank=True, null=True)
    references = models.ManyToManyField(ReferenceLink, default=None, blank=True)
    description = models.TextField(default=None, blank=True, null=True)
    has_outdoor_seating = models.BooleanField(verbose_name="Outdoor Seating?")
    is_temp_closed = models.BooleanField(verbose_name="Temporarily closed?")
    is_eats = models.BooleanField(verbose_name="Eats")
    is_drinks = models.BooleanField(verbose_name="Drinks")
    is_coffee = models.BooleanField(verbose_name="Coffees")
    is_food_hall = models.BooleanField(verbose_name="Food Hall?", default=False)
    not_local = models.BooleanField(verbose_name="Not local?")
    open_date = models.DateField(null=True, blank=True)
    added = models.BooleanField(verbose_name="Added to Eats?")

    @property
    def is_new_tip(self):
        today = datetime.date.today()
        if today < self.date + datetime.timedelta(days=14):
            return True
        return False

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
