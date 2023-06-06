from arcgis2geojson import arcgis2geojson
import requests
from django.core.serializers import serialize
from django.shortcuts import render

from django.views.decorators.clickjacking import xframe_options_exempt

from newBernTOD.models import Overlay
from develop.views import get_ncod_data


def get_hod1_data():
    # General Historic Overlay Districts
    url = "https://maps.raleighnc.gov/arcgis/rest/services/Planning/Overlays/MapServer/7/query?outFields=*&where=1" \
          "%3D1&f=geojson"

    return requests.request("GET", url, headers={}, data={})


def get_hod2_data():
    # Streetside Historic Overlay Districts
    url = "https://maps.raleighnc.gov/arcgis/rest/services/Planning/Overlays/MapServer/8/query?outFields=*&where=1" \
          "%3D1&f=geojson"

    return requests.request("GET", url, headers={}, data={})


@xframe_options_exempt
def tod(request):
    ncod_response = get_ncod_data()
    ncod_data = arcgis2geojson(ncod_response.json())

    hod1_response = get_hod1_data()
    hod1_data = arcgis2geojson(hod1_response.json())
    hod2_response = get_hod2_data()
    hod2_data = arcgis2geojson(hod2_response.json())

    new_bern_tod = Overlay.objects.get(name="New Bern TOD")
    output_geojson = serialize("geojson", new_bern_tod.parcels.all(),
                               geometry_field="geom",
                               fields=("property_address",))

    return render(request, "tod.html", {"tod_zoning_data": output_geojson,
                                        "ncod_data": ncod_data,
                                        "hod1_data": hod1_response.json(),
                                        "hod2_data": hod2_data})
