from arcgis2geojson import arcgis2geojson
from django.core.serializers import serialize
from django.shortcuts import render

from django.views.decorators.clickjacking import xframe_options_exempt

from newBernTOD.models import Overlay
from develop.views import get_ncod_data


@xframe_options_exempt
def tod(request):
    ncod_response = get_ncod_data()
    ncod_data = arcgis2geojson(ncod_response.json())

    # output_geojson = serialize("geojson", Parcel.objects.all(),
    #                            geometry_field="geom",
    #                            fields=("property_address",))
    new_bern_tod = Overlay.objects.get(name="New Bern TOD")
    output_geojson = serialize("geojson", new_bern_tod.parcels.all(),
                               geometry_field="geom",
                               fields=("property_address",))

    return render(request, "tod.html", {"tod_zoning_data": output_geojson,
                                        "ncod_data": ncod_data})
