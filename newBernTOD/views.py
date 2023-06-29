from arcgis2geojson import arcgis2geojson
import requests
from django.core.serializers import serialize
from django.shortcuts import render

from django.views.decorators.clickjacking import xframe_options_exempt

from newBernTOD.models import Overlay, Parcel, NCOD, HOD
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
                               fields=("property_address", "curr_zoning", "prop_zoning"))

    new_bern_rezoning = Overlay.objects.get(name="Not TOD but Rezoned")
    rezoning_geojson = serialize("geojson", new_bern_rezoning.parcels.all(),
                                 geometry_field="geom",
                                 fields=("property_address", "curr_zoning", "prop_zoning"))

    nbe_ncod = NCOD.objects.filter(olay_name__icontains="New Bern - Edenton")
    nbe_ncod_output_geojson = serialize("geojson", nbe_ncod, geometry_field="geom")

    oakwood_park_ncod = NCOD.objects.get(olay_name="Oakwood Park")
    oakwood_park_output_geojson = serialize("geojson", [oakwood_park_ncod], geometry_field="geom")

    south_park_ncod = NCOD.objects.get(olay_name="South Park")
    south_park_output_geojson = serialize("geojson", [south_park_ncod], geometry_field="geom")

    mordecai_ncod = NCOD.objects.filter(olay_name__icontains="Mordecai")
    mordecai_output_geojson = serialize("geojson", mordecai_ncod, geometry_field="geom")

    king_ncod = NCOD.objects.filter(olay_name="King Charles (South)")
    king_charles_output_geojson = serialize("geojson", king_ncod, geometry_field="geom")

    oakwood_hod = HOD.objects.get(olay_name="Oakwood")
    oakwood_output_geojson = serialize("geojson", [oakwood_hod], geometry_field="geom")

    blount_street_hod = HOD.objects.get(olay_name="Blount Street")
    blount_street_output_geojson = serialize("geojson", [blount_street_hod], geometry_field="geom")

    capitol_hod = HOD.objects.get(olay_name="Capitol Square")
    capitol_output_geojson = serialize("geojson", [capitol_hod], geometry_field="geom")

    moore_hod = HOD.objects.get(olay_name="Moore Square")
    moore_output_geojson = serialize("geojson", [moore_hod], geometry_field="geom")

    prince_hod = HOD.objects.get(olay_name="Prince Hall")
    prince_output_geojson = serialize("geojson", [prince_hod], geometry_field="geom")

    return render(request, "filtered_tod.html", {"tod_zoning_data": output_geojson,
                                                 "rezoning_geojson": rezoning_geojson,
                                                 "nbe_ncod": nbe_ncod_output_geojson,
                                                 "oakwood_park_output_geojson": oakwood_park_output_geojson,
                                                 "south_park_output_geojson": south_park_output_geojson,
                                                 "mordecai_output_geojson": mordecai_output_geojson,
                                                 "king_charles_output_geojson": king_charles_output_geojson,
                                                 "oakwood_hod": oakwood_output_geojson,
                                                 "blount_hod": blount_street_output_geojson,
                                                 "capitol_output_geojson": capitol_output_geojson,
                                                 "moore_output_geojson": moore_output_geojson,
                                                 "prince_output_geojson": prince_output_geojson
                                                 })


@xframe_options_exempt
def show_all_parcels(request):
    all_parcels = serialize("geojson", Parcel.objects.all(), geometry_field="geom")

    return render(request, "all_parcels.html", {"all_parcels": all_parcels})


@xframe_options_exempt
def show_ncod_by_id(request, ncod_id):
    ncod_overlay = NCOD.objects.prefetch_related("parcels").get(id=ncod_id)
    tod_overlay = Overlay.objects.prefetch_related("parcels").get(name="New Bern TOD")

    ncod_by_id_data_geojson = serialize("geojson", [ncod_overlay],
                                        geometry_field="geom",
                                        fields=("olay_name", "pin",))

    all_parcels_in_the_overlay_geojson = serialize("geojson", ncod_overlay.parcels.all(),
                                                   geometry_field="geom",
                                                   fields=("olay_name", "pin",))

    tod_parcels_in_overlay = [p for p in ncod_overlay.parcels.all() if p in tod_overlay.parcels.all()]
    tod_parcels_that_intersect_geojson = serialize("geojson", tod_parcels_in_overlay,
                                                   geometry_field="geom",
                                                   fields=("olay_name", "pin",))

    return render(request, "overlay_by_id.html",
                  {"overlay_by_id_data_geojson": ncod_by_id_data_geojson,
                   "all_parcels_in_the_overlay_geojson": all_parcels_in_the_overlay_geojson,
                   "tod_parcels_that_intersect_geojson": tod_parcels_that_intersect_geojson,
                   "overlay": ncod_overlay,
                   "count": str(len(tod_parcels_in_overlay))})


@xframe_options_exempt
def show_ncod_by_name(request, ncod_name):
    ncod_overlay = NCOD.objects.prefetch_related("parcels").filter(olay_name=ncod_name)
    if ncod_overlay.count() == 0:
        ncod_overlay = Overlay.objects.prefetch_related("parcels").filter(olay_name=ncod_name)

    tod_overlay = Overlay.objects.prefetch_related("parcels").get(name="New Bern TOD")

    ncod_by_name_data_geojson = serialize("geojson", ncod_overlay,
                                          geometry_field="geom", fields=("olay_name", "pin",))

    combined = []
    for ncod_piece in ncod_overlay:
        combined += [parcel for parcel in ncod_piece.parcels.all()]
    all_parcels_in_the_overlay_geojson = serialize("geojson", combined,
                                                   geometry_field="geom",
                                                   fields=("olay_name", "pin",))

    tod_parcels_in_overlay = [p for p in combined if p in tod_overlay.parcels.all()]
    tod_parcels_that_intersect_geojson = serialize("geojson", tod_parcels_in_overlay,
                                                   geometry_field="geom",
                                                   fields=("olay_name", "pin",))

    return render(request, "overlay_by_id.html",
                  {"overlay_by_id_data_geojson": ncod_by_name_data_geojson,
                   "all_parcels_in_the_overlay_geojson": all_parcels_in_the_overlay_geojson,
                   "tod_parcels_that_intersect_geojson": tod_parcels_that_intersect_geojson,
                   "overlay": ncod_overlay[0],
                   "count": str(len(tod_parcels_in_overlay))})


@xframe_options_exempt
def show_hod_by_name(request, hod_name):
    hod_overlay = HOD.objects.prefetch_related("parcels").get(olay_name=hod_name)
    tod_overlay = Overlay.objects.prefetch_related("parcels").get(name="New Bern TOD")

    hod_by_name_data_geojson = serialize("geojson", [hod_overlay],
                                         geometry_field="geom", fields=("olay_name", "pin",))

    all_parcels_in_the_overlay_geojson = serialize("geojson", hod_overlay.parcels.all(),
                                                   geometry_field="geom",
                                                   fields=("olay_name", "pin",))

    tod_parcels_in_overlay = [p for p in hod_overlay.parcels.all() if p in tod_overlay.parcels.all()]
    tod_parcels_that_intersect_geojson = serialize("geojson", tod_parcels_in_overlay,
                                                   geometry_field="geom",
                                                   fields=("olay_name", "pin",))

    return render(request, "overlay_by_id.html",
                  {"overlay_by_id_data_geojson": hod_by_name_data_geojson,
                   "all_parcels_in_the_overlay_geojson": all_parcels_in_the_overlay_geojson,
                   "tod_parcels_that_intersect_geojson": tod_parcels_that_intersect_geojson,
                   "overlay": hod_overlay,
                   "count": str(len(tod_parcels_in_overlay))})


@xframe_options_exempt
def show_all_parcels_in_ncod(request, ncod_id):
    ncod_to_show = NCOD.objects.get(id=ncod_id)
    ncod_data = serialize("geojson", [p for p in ncod_to_show.parcels.all()],
                          geometry_field="geom",
                          fields=("OLAY_NAME", "pin",))

    return render(request, "all_parcels.html", {"all_parcels": ncod_data})


@xframe_options_exempt
def new_bern_main(request):
    new_bern_area_ncod_names = ["King Charles (South)", "Oakwood Park", "South Park"]
    new_bern_area_overlay_names = ["Mordecai", "New Bern - Edenton"]
    new_bern_area_hod_names = ["Oakwood", "Prince Hall", "Moore Square", "Capitol Square", "Blount Street"]

    new_bern_ncods = []
    for ncod_name in new_bern_area_ncod_names:
        ncods = NCOD.objects.filter(olay_name__icontains=ncod_name)
        for ncod in ncods:
            new_bern_ncods.append(ncod)
    for ncod_overlay_name in new_bern_area_overlay_names:
        ncod_overlays = Overlay.objects.filter(olay_name__icontains=ncod_overlay_name, overlay="NCOD")
        for ncod in ncod_overlays:
            new_bern_ncods.append(ncod)

    new_bern_hods = []
    for hod_name in new_bern_area_hod_names:
        hods = HOD.objects.filter(olay_name__icontains=hod_name)
        for hod in hods:
            new_bern_hods.append(hod)

    new_bern_tod = Overlay.objects.get(name="New Bern TOD")

    return render(request, "new_bern_main.html", {"new_bern_overlay_ncods": new_bern_ncods,
                                                  "new_bern_overlay_hods": new_bern_hods,
                                                  "new_bern_tod": new_bern_tod})
