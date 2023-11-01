from django.shortcuts import render
from django_tables2 import SingleTableView, Column

from parcels.history import get_parcel_history_diffs, get_parcel_history_table_headers, get_parcel_history_table_data
from parcels.location import get_parcels_from_point
from parcels.models import Parcel
from parcels.tables import ParcelHistoryTable

page_title = "Parcel Tracking"


def main(request):
    lat = None
    lon = None
    lat_string_from_form = request.GET.get("lat_input")
    lon_string_from_form = request.GET.get("lon_input")
    if lat_string_from_form:
        lat = float(lat_string_from_form)
    if lon_string_from_form:
        lon = float(lon_string_from_form)

    target_parcels = get_parcels_from_point(lat, lon)

    # [['parcel_inst1', 'parcel_inst1_table'], ['parcel_inst2', 'parcel_inst2_table'], .....]
    all_parcel_data = []

    for parcel in target_parcels:
        parcel_history = parcel.history.all()
        parcel_history_diffs_list = get_parcel_history_diffs(parcel_history)

        parcel_history_table_headers = get_parcel_history_table_headers(parcel_history_diffs_list)
        table_headers_add_list = [(header_name, Column()) for header_name in parcel_history_table_headers]
        if table_headers_add_list:
            table = ParcelHistoryTable(target_parcels[0].history.all(), extra_columns=table_headers_add_list)
        else:
            table = None

        all_parcel_data.append([parcel, table])

    return render(request, "parcel_main.html", {"page_title": page_title,
                                                "lat_input": lat,
                                                "lon_input": lon,
                                                "all_parcel_data": all_parcel_data})


class ParcelHistoryView(SingleTableView):
    model = Parcel
    table_class = ParcelHistoryTable
    template_name = "parcel_main.html"
