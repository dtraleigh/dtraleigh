from django.shortcuts import render
from datetime import datetime

from parking.models import ParkingLocation


def get_today_day_of_week():
    return datetime.now().strftime("%A")


def get_parking_datasets(parking_locations_to_show):
    datasets = [{
        "label": "free",
        "backgroundColor": "green",
        "data": [],
        "barPercentage": 0.9,
    }, {
        "label": "charge",
        "backgroundColor": "orange",
        "data": [],
        "barPercentage": 0.9,
    }, {
        "label": "free",
        "backgroundColor": "green",
        "data": [],
        "barPercentage": 0.9,
    }]

    for location in parking_locations_to_show:
        todays_rates = location.rate_schedule.first().rates.filter(day_of_week=get_today_day_of_week().upper())

        for count, rate in enumerate(todays_rates):
            datasets[count]["data"].append({"x": rate.end_time.hour - rate.start_time.hour, "rate": rate.rate})

    return datasets


def main(request):
    day_of_the_week = get_today_day_of_week()
    parking_locations_to_show = ParkingLocation.objects.all()

    parking_locations = [f"\'{loc.name}\'" for loc in parking_locations_to_show]
    parking_locations_string = ", ".join(parking_locations)

    datasets = get_parking_datasets(parking_locations_to_show)

    return render(request, "parking_main.html", {"day_of_the_week": day_of_the_week,
                                                 "parking_locations": parking_locations_string,
                                                 "datasets": datasets})
