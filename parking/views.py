from django.shortcuts import render
from datetime import datetime
import pytz

from parking.models import ParkingLocation


def get_today_day_of_week():
    est = pytz.timezone('US/Eastern')
    est_time = datetime.now(est)
    return est_time.strftime("%A").upper()


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
        todays_rates = location.get_todays_rates(day_of_week)

        for count, rate in enumerate(todays_rates):
            if rate.all_day and rate.is_free:
                datasets[0]["data"].append({"x": 23, "rate": f"{rate.get_rate_display()} all day"})
                datasets[1]["data"].append({})
                datasets[2]["data"].append({})
                break
            elif rate.all_day:
                datasets[0]["data"].append({})
                datasets[1]["data"].append({"x": 23, "rate": f"{rate.get_rate_display()} all day"})
                datasets[2]["data"].append({})
                break
            else:
                datasets[count]["data"].append({"x": rate.end_time.hour - rate.start_time.hour,
                                                "rate": rate.get_rate_display()})

    return datasets


def main(request):
    day_of_the_week = "MONDAY"  # Used for debugging
    # day_of_the_week = get_today_day_of_week()
    parking_locations_to_show = ParkingLocation.objects.exclude(rate_schedule=None)

    parking_locations = [f"\'{loc.get_type_display()}: {loc.name} {loc.get_cost_display()}\'"
                         for loc in parking_locations_to_show]
    parking_locations_string = ", ".join(parking_locations)

    datasets = get_parking_datasets(parking_locations_to_show, day_of_the_week)

    return render(request, "parking_main.html", {"day_of_the_week": day_of_the_week,
                                                 "parking_locations": parking_locations_string,
                                                 "datasets": datasets})
