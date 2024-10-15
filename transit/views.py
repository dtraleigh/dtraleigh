from django.shortcuts import render
from django.core.serializers import serialize
from django.views.decorators.clickjacking import xframe_options_exempt

from transit.models import ShapefileRoute, GTFSRoute
from django.db.models import Q


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


@xframe_options_exempt
def main(request):
    all_transit_data = serialize("geojson",
                                 ShapefileRoute.objects.all(),
                                 geometry_field="geom",
                                 fields=("line_name", "route_color"))

    return render(request, "transit_main.html", {"all_transit_data": all_transit_data})


@xframe_options_exempt
def high_frequency(request, day_of_the_week):
    all_transit_data = serialize("geojson",
                                 get_high_frequency_shapefile_routes(day_of_the_week),
                                 geometry_field="geom",
                                 fields=("line_name", "route_color"))

    return render(request, "transit_main.html", {"all_transit_data": all_transit_data})
