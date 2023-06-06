from django.shortcuts import render
import requests
from django.core.serializers import serialize
from develop.models import TrackArea
from arcgis2geojson import arcgis2geojson
from django.views.decorators.clickjacking import xframe_options_exempt


def get_ncod_data():
    url = "https://maps.raleighnc.gov/arcgis/rest/services/Planning/Overlays/MapServer/9/query?where=1%3D1&outFields" \
          "=*&outSR=4326&f=json"

    # headers = {
    #     "Cookie": 'AGS_ROLES="419jqfa+uOZgYod4xPOQ8Q=="'
    # }

    return requests.request("GET", url, headers={}, data={})


@xframe_options_exempt
def itb(request):
    itb_data = serialize("geojson", TrackArea.objects.all(), geometry_field="geom", fields=("long_name",))

    return render(request, "itb.html", {"itb_data": itb_data})


@xframe_options_exempt
def ncod(request):
    ncod_response = get_ncod_data()
    ncod_data = arcgis2geojson(ncod_response.json())

    return render(request, "ncod.html", {"ncod_data": ncod_data})


@xframe_options_exempt
def dx_zoning(request):
    url = "https://maps.raleighnc.gov/arcgis/rest/services/Planning/Zoning/MapServer/0/query?outFields=*&outSR=4326&f" \
          "=json&where=ZONE_TYPE='DX-'"

    headers = {
        "Cookie": 'AGS_ROLES="419jqfa+uOZgYod4xPOQ8Q=="'
    }

    response = requests.request("GET", url, headers=headers, data={})

    dx_zoning_data = arcgis2geojson(response.json())

    return render(request, "dx.html", {"dx_zoning_data": dx_zoning_data})


@xframe_options_exempt
def dx_zoning40(request):
    # Keep this on one line unless you want to investigate why it doesn't work when on two.
    url = "https://maps.raleighnc.gov/arcgis/rest/services/Planning/Zoning/MapServer/0/query?outFields=*&outSR=4326&f=json&where=HEIGHT>30 AND ZONE_TYPE='DX-'"

    payload = {}
    headers = {
        "Cookie": 'AGS_ROLES="419jqfa+uOZgYod4xPOQ8Q=="'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    dx40_zoning_data = arcgis2geojson(response.json())

    return render(request, "dx.html", {"dx_zoning_data": dx40_zoning_data})
