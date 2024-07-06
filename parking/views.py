from django.shortcuts import render
from datetime import datetime
import pytz

from parking.models import ParkingLocation


def get_today_day_of_week():
    est = pytz.timezone('US/Eastern')
    est_time = datetime.now(est)
    return est_time.strftime("%A").upper()


def get_rate_color(rate):
    if rate.is_free:
        return "MediumSeaGreen"
    elif not rate.is_free and rate.rate == "HOURLY_RATES":
        return "pattern.draw('diagonal', 'Tomato')"
    elif not rate.is_free and rate.rate == "WEEKEND_FLAT":
        return "YellowGreen"


def get_parking_datasets(parking_locations_to_show, day_of_week):
    datasets = [{
        "label": "free",
        "data": [],
        "barPercentage": 0.9,
    }, {
        "label": "charge",
        "data": [],
        "barPercentage": 0.9,
    }, {
        "label": "free",
        "data": [],
        "barPercentage": 0.9,
    }]

    for location in parking_locations_to_show:
        todays_rates = location.rate_schedule.first().rates.filter(day_of_week=day_of_week)

        for count, rate in enumerate(todays_rates):
            if rate.all_day and rate.is_free:
                datasets[count]["data"].append({"x": 23, "rate": f"{rate.get_rate_display()} all day"})
            else:
                datasets[count]["data"].append({"x": rate.end_time.hour - rate.start_time.hour,
                                                "rate": rate.get_rate_display()})

    return datasets


def main(request):
    day_of_the_week = "MONDAY"  # Used for debugging
    # day_of_the_week = get_today_day_of_week()
    parking_locations_to_show = ParkingLocation.objects.all()

    parking_locations = [f"\'{loc.name}\'" for loc in parking_locations_to_show]
    parking_locations_string = ", ".join(parking_locations)

    datasets = get_parking_datasets(parking_locations_to_show, day_of_the_week)

    return render(request, "parking_main.html", {"day_of_the_week": day_of_the_week,
                                                 "parking_locations": parking_locations_string,
                                                 "datasets": datasets})
