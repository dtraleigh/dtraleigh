from django.shortcuts import render
from django.core.serializers import serialize
from django.views.decorators.clickjacking import xframe_options_exempt

from transit.models import ShapefileRoute, GTFSRoute
from django.db.models import Q
import datetime


def time_to_decimal(time_obj):
    if not isinstance(time_obj, datetime.time):
        raise ValueError("Input must be a datetime.time object")

    hours = time_obj.hour
    minutes = time_obj.minute
    decimal_time = hours + minutes / 60.0
    return decimal_time


def get_high_frequency_shapefile_routes(day_of_week):
    high_frequency_routes = GTFSRoute.objects.all()
    high_frequency_routes = [
        route for route in high_frequency_routes if route.is_high_frequency(day_of_week)
    ]

    high_frequency_shapefile_routes = ShapefileRoute.objects.filter(
        Q(gtfsroute__in=high_frequency_routes),
        is_enabled=True
    ).distinct()

    return high_frequency_shapefile_routes


def get_high_frequency_gtfs_routes(day_of_week):
    all_routes = GTFSRoute.objects.filter(is_enabled=True)
    high_frequency_routes = []

    for route in all_routes:
        if route.is_high_frequency(day_of_week):
            high_frequency_routes.append(route.id)

    return GTFSRoute.objects.filter(id__in=high_frequency_routes)


@xframe_options_exempt
def main(request):
    all_transit_data = serialize("geojson",
                                 ShapefileRoute.objects.all(),
                                 geometry_field="geom",
                                 fields=("line_name", "route_color", "dir_name"))
    legend_title = "All Routes"

    return render(request, "transit_main.html", {"all_transit_data": all_transit_data,
                                                 "legend_title": legend_title})


@xframe_options_exempt
def high_frequency(request, day_of_the_week):
    # Dynamic, if we ever need to update the data
    # high_freq_routes = get_high_frequency_shapefile_routes(day_of_the_week)

    # Static, cheap fix for faster load times
    if day_of_the_week == 'saturday':
        high_freq_route_ids = [8, 7, 2, 1, 62, 61, 83, 84]
    elif day_of_the_week == 'sunday':
        high_freq_route_ids = [8, 7, 2, 1, 83, 84]
    else:
        high_freq_route_ids = [64, 63, 44, 43, 60, 59, 8, 7, 2, 1, 62, 61, 74, 73, 83, 84]
    high_freq_routes = ShapefileRoute.objects.filter(id__in=high_freq_route_ids)

    all_transit_data = serialize("geojson",
                                 high_freq_routes,
                                 geometry_field="geom",
                                 fields=("line_name", "route_color", "dir_name"))
    legend_title = "High Frequency Routes"

    return render(request, "transit_main.html", {"all_transit_data": all_transit_data,
                                                 "legend_title": legend_title})


@xframe_options_exempt
def high_frequency_chart(request, day_of_the_week):
    high_frequency_GTFS_routes = get_high_frequency_gtfs_routes(day_of_the_week)
    high_frequency_GTFS_route_chart_data = []

    for route in high_frequency_GTFS_routes:
        # Example ["Route 1", 6, 20],  // Route 1 service from 6 AM to 8 PM
        high_frequency_GTFS_route_chart_data.append([f"{route.route_short_name} - {route.route_long_name}",
                                                     time_to_decimal(route.start_high_frequency(day_of_the_week)),
                                                     time_to_decimal(route.stop_high_frequency(day_of_the_week))])

    return render(request, "transit_chart.html",
                  {"high_frequency_GTFS_route_chart_data": high_frequency_GTFS_route_chart_data})
