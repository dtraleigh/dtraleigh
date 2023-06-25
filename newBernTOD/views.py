from arcgis2geojson import arcgis2geojson
import requests
from django.core.serializers import serialize
from django.shortcuts import render

from django.views.decorators.clickjacking import xframe_options_exempt

from newBernTOD.models import Overlay, Parcel
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


@xframe_options_exempt
def filter_tod(request):
    new_bern_tod = Overlay.objects.get(name="New Bern TOD")
    output_geojson = serialize("geojson", new_bern_tod.parcels.all(),
                               geometry_field="geom",
                               fields=("property_address",))

    nbe_ncod = Overlay.objects.get(name="Combined New Bern - Edenton NCOD")
    # nbe_ncod_output_geojson = serialize("geojson", nbe_ncod.parcels.all(),
    #                                     geometry_field="geom",
    #                                     fields=("property_address",))
    nbe_ncod_output_geojson = serialize("geojson", [nbe_ncod], geometry_field="geom")

    oakwood_hod = Overlay.objects.get(OLAY_NAME="Oakwood")
    # oakwood_output_geojson = serialize("geojson", oakwood_hod.parcels.all(),
    #                                    geometry_field="geom",
    #                                    fields=("property_address",))
    oakwood_output_geojson = serialize("geojson", [oakwood_hod], geometry_field="geom")

    blount_street_hod = Overlay.objects.get(OLAY_NAME="Blount Street")
    blount_street_output_geojson = serialize("geojson", [blount_street_hod], geometry_field="geom")

    capitol_hod = Overlay.objects.get(OLAY_NAME="Capitol Square")
    capitol_output_geojson = serialize("geojson", [capitol_hod], geometry_field="geom")

    moore_hod = Overlay.objects.get(OLAY_NAME="Moore Square")
    moore_output_geojson = serialize("geojson", [moore_hod], geometry_field="geom")

    prince_hod = Overlay.objects.get(OLAY_NAME="Prince Hall")
    prince_output_geojson = serialize("geojson", [prince_hod], geometry_field="geom")

    oakwood_park_ncod = Overlay.objects.get(OLAY_NAME="Oakwood Park")
    oakwood_park_output_geojson = serialize("geojson", [oakwood_park_ncod], geometry_field="geom")

    south_park_ncod = Overlay.objects.get(OLAY_NAME="South Park")
    south_park_output_geojson = serialize("geojson", [south_park_ncod], geometry_field="geom")

    mordecai_ncod = Overlay.objects.filter(OLAY_NAME__contains="Mordecai")
    mordecai_output_geojson = serialize("geojson", mordecai_ncod, geometry_field="geom")

    return render(request, "filtered_tod.html", {"tod_zoning_data": output_geojson,
                                                 "nbe_ncod": nbe_ncod_output_geojson,
                                                 "oakwood_hod": oakwood_output_geojson,
                                                 "blount_hod": blount_street_output_geojson,
                                                 "capitol_output_geojson": capitol_output_geojson,
                                                 "moore_output_geojson": moore_output_geojson,
                                                 "prince_output_geojson": prince_output_geojson,
                                                 "oakwood_park_output_geojson": oakwood_park_output_geojson,
                                                 "south_park_output_geojson": south_park_output_geojson,
                                                 "mordecai_output_geojson": mordecai_output_geojson})


@xframe_options_exempt
def show_all_parcels(request):
    all_parcels = serialize("geojson", Parcel.objects.all(), geometry_field="geom")

    return render(request, "all_parcels.html", {"all_parcels": all_parcels})


@xframe_options_exempt
def show_overlay_by_id(request, overlay_id):
    overlay_data = serialize("geojson", [Overlay.objects.get(id=overlay_id)],
                             geometry_field="geom",
                             fields=("OLAY_NAME",))

    return render(request, "all_parcels.html", {"all_parcels": overlay_data})


@xframe_options_exempt
def show_all_parcels_in_overlay(request, overlay_id):
    overlay_to_show = Overlay.objects.get(id=overlay_id)
    overlay_data = serialize("geojson", [p for p in overlay_to_show.parcels.all()],
                             geometry_field="geom",
                             fields=("OLAY_NAME",))

    return render(request, "all_parcels.html", {"all_parcels": overlay_data})


def get_combined_new_bern_edenton_ncod():
    if not Overlay.objects.filter(name="Combined New Bern - Edenton NCOD").exists():
        NBE_overlays = Overlay.objects.filter(OLAY_NAME="New Bern - Edenton")
        geom_union = NBE_overlays[0].geom
        geom_union = geom_union.union(NBE_overlays[1].geom)

        all_parcels_combined = [a for a in NBE_overlays[0].parcels.all()] + [b for b in NBE_overlays[1].parcels.all()]

        NBE = Overlay.objects.create(name="Combined New Bern - Edenton NCOD",
                                     OLAY_NAME="New Bern - Edenton",
                                     description="This overlay combines the two NCOD polygons for New-Bern Edenton",
                                     geom=geom_union)
        NBE.parcels.set(all_parcels_combined)
        return Overlay.objects.get(name="Combined New Bern - Edenton NCOD")
    else:
        return Overlay.objects.get(name="Combined New Bern - Edenton NCOD")


@xframe_options_exempt
def new_bern_main(request):
    new_bern_area_overlay_names = [
        "Oakwood",
        "Blount Street",
        "Capitol Square",
        "Moore Square",
        "Prince Hall",
        "King Charles(South)",
        "New Bern - Edenton",
        "South Park",
        "Oakwood Park",
        # "Mordecai 1",
        # "Mordecai 2"
    ]

    new_bern_ncod_overlays = Overlay.objects.filter(OLAY_NAME__in=new_bern_area_overlay_names, OVERLAY="NCOD")

    # Mordecai has 3 overlays. New Bern - Edenton has 2
    new_bern_overlay_ncods = []
    to_skip = ["New Bern - Edenton", "Mordecai 1", "Mordecai 2"]
    for overlay in new_bern_ncod_overlays:
        if overlay.OLAY_NAME not in to_skip:
            new_bern_overlay_ncods.append(overlay)

    new_bern_overlay_ncods.append(get_combined_new_bern_edenton_ncod())

    new_bern_hod_overlays = Overlay.objects.filter(OLAY_NAME__in=new_bern_area_overlay_names, OVERLAY__contains="HOD")

    new_bern_tod = Overlay.objects.get(name="New Bern TOD")

    return render(request, "new_bern_main.html", {"new_bern_ncod_overlays": new_bern_ncod_overlays,
                                                  "new_bern_overlay_ncods": new_bern_overlay_ncods,
                                                  "new_bern_overlay_hods": new_bern_hod_overlays,
                                                  "new_bern_tod": new_bern_tod})
