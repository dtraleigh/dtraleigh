from django.db import models


class Rate(models.Model):
    days_of_week = (("MONDAY", "Monday"),
                    ("TUESDAY", "Tuesday"),
                    ("WEDNESDAY", "Wednesday"),
                    ("THURSDAY", "Thursday"),
                    ("FRIDAY", "Friday"),
                    ("SATURDAY", "Saturday"),
                    ("SUNDAY", "Sunday"))
    rate_information = (("FREE", "Free"),
                        ("FREE_EVENING", "Free Evenings"),
                        ("HOURLY_RATES", "Hourly Rates Apply"),
                        ("WEEKEND_FLAT", "$5 Flat Fee"))

    day_of_week = models.CharField(choices=days_of_week,
                                   blank=True,
                                   default=None,
                                   verbose_name="Day of Week",
                                   max_length=100)
    rate = models.CharField(choices=rate_information,
                            blank=True,
                            default=None,
                            verbose_name="Rate/Fee",
                            max_length=100)
    all_day = models.BooleanField(default=False)
    is_free = models.BooleanField(default=False)
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)

    class Meta:
        ordering = ["start_time"]

    def __str__(self):
        return f"Rate (id:{self.id}) - {self.day_of_week}: {self.start_time}-{self.end_time} - {self.rate}"


class RateSchedule(models.Model):
    name = models.CharField(max_length=400)
    rates = models.ManyToManyField(Rate, blank=True)

    def __str__(self):
        return f"RateSchedule (id:{self.id}) - {self.name}"


class ParkingLocation(models.Model):
    parking_location_types = (("DECK", "Deck"),
                              ("LOT", "Lot"))

    name = models.CharField(max_length=400)
    type = models.CharField(choices=parking_location_types,
                            blank=True,
                            default=None,
                            verbose_name="Parking Location Type",
                            max_length=100)
    owner = models.CharField(max_length=400)
    url = models.TextField(blank=True, null=True, verbose_name="Parking information URL")
    special_event_capable = models.BooleanField(default=False)
    rate_schedule = models.ManyToManyField(RateSchedule, default=None, blank=True)

    def __str__(self):
        return f"ParkingLocation (id:{self.id}) - {self.name}"
