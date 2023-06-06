from arcgis2geojson import arcgis2geojson
import requests
from django.core.serializers import serialize
from django.shortcuts import render

from django.views.decorators.clickjacking import xframe_options_exempt

from newBernTOD.models import Overlay
from develop.views import get_ncod_data


def get_hod_data():
    # General Historic Overlay Districts
    gen_hod_url = "https://maps.raleighnc.gov/arcgis/rest/services/Planning/Overlays/MapServer/7/query?outFields" \
                  "=*&where=1%3D1&f=geojson"
    # Streetside Historic Overlay Districts
    str_hod_url = "https://maps.raleighnc.gov/arcgis/rest/services/Planning/Overlays/MapServer/8/query?outFields" \
                  "=*&where=1%3D1&f=geojson"

    gen_hod_response = requests.request("GET", gen_hod_url, headers={}, data={})
    str_hod_response = requests.request("GET", str_hod_url, headers={}, data={})

    merged = gen_hod_response.json()
    for feature in str_hod_response.json()["features"]:
        merged["features"].append(feature)

    return merged


@xframe_options_exempt
def tod(request):
    ncod_response = get_ncod_data()
    ncod_data = arcgis2geojson(ncod_response.json())

    hod_data = get_hod_data()

    new_bern_tod = Overlay.objects.get(name="New Bern TOD")
    output_geojson = serialize("geojson", new_bern_tod.parcels.all(),
                               geometry_field="geom",
                               fields=("property_address",))

    return render(request, "tod.html", {"tod_zoning_data": output_geojson,
                                        "ncod_data": ncod_data,
                                        "hod_data": hod_data})
