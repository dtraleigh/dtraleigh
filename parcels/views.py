from django.shortcuts import render

from parcels.location import get_parcels_from_point


def main(request):
    lat_string_from_form = request.GET.get("lat_input")
    lat = float(lat_string_from_form)
    lon_string_from_form = request.GET.get("lon_input")
    lon = float(lon_string_from_form)

    main_parcels = get_parcels_from_point(lat, lon)

    return render(request, "parcel_main.html", {"main_parcels": main_parcels})
