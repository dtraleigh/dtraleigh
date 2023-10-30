from django.shortcuts import render
from django.views.generic import ListView
from django_tables2 import SingleTableView, Column

from parcels.history import get_parcel_history_diffs, get_parcel_history_table_headers, get_parcel_history_table_data
from parcels.location import get_parcels_from_point
from parcels.models import Parcel
from parcels.tables import ParcelHistoryTable


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
        parcel_ind_data = [parcel]

        # parcel_history = parcel.history.all()
        # parcel_history_diffs_list = get_parcel_history_diffs(parcel_history)
        #
        # parcel_history_table_headers = get_parcel_history_table_headers(parcel_history_diffs_list)
        # parcel_history_table_headers.insert(0, "created_date")
        #
        # parcel_history_table_data = get_parcel_history_table_data(parcel_history_diffs_list,
        #                                                           parcel_history_table_headers)
        table = ParcelHistoryTable(target_parcels[0].history.all(), extra_columns=[("land_val", Column())])
        parcel_ind_data.append(table)
        all_parcel_data.append(parcel_ind_data)

    return render(request, "parcel_main.html", {"all_parcel_data": all_parcel_data})


class ParcelHistoryView(SingleTableView):
    model = Parcel
    table_class = ParcelHistoryTable
    template_name = "parcel_main.html"
