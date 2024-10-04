from django.shortcuts import render
from django.core.serializers import serialize
from django.views.decorators.clickjacking import xframe_options_exempt

from transit.models import BusRoute


@xframe_options_exempt
def main(request):
    all_transit_data = serialize("geojson",
                                 BusRoute.objects.all(),
                                 geometry_field="geom",
                                 fields=("full_name", "route_color"))

    return render(request, "transit_main.html", {"all_transit_data": all_transit_data})
