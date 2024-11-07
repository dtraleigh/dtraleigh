import json

from django.core.paginator import Paginator
from django.core.serializers import serialize
from django.shortcuts import render
from django_tables2 import SingleTableView, Column

from parcels.history import get_parcel_history_diffs, get_parcel_history_table_headers
from parcels.functions import get_parcels_from_point, get_parcel_historical_from_point
from parcels.models import Parcel, RaleighSubsection, ParcelHistorical
from parcels.tables import ParcelHistoryTable

page_title = "Parcel Tracking"


def get_lat_lon_from_request(request):
    lat = None
    lon = None
    lat_string_from_form = request.GET.get("lat_input")
    lon_string_from_form = request.GET.get("lon_input")
    if lat_string_from_form:
        lat = float(lat_string_from_form)
    if lon_string_from_form:
        lon = float(lon_string_from_form)
    return lat, lon


def main(request):
    lat, lon = get_lat_lon_from_request(request)
    target_parcels = get_parcel_historical_from_point(lat, lon)

    # [['parcel_inst1', 'parcel_inst1_table'], ['parcel_inst2', 'parcel_inst2_table'], .....]
    all_parcel_data = []

    for parcel in target_parcels:
        table = None
        all_parcel_data.append([parcel, table])

    return render(request, "parcel_main_historical.html", {"page_title": page_title,
                                                           "lat_input": lat,
                                                           "lon_input": lon,
                                                           "all_parcel_data": all_parcel_data})


def main_backup(request):
    lat, lon = get_lat_lon_from_request(request)
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


def history(request):
    lat, lon = get_lat_lon_from_request(request)
    # target_parcels = get_parcel_historical_from_point(lat, lon)
    # test_list = [314374, 635498, 956622, 1277746, 1598870, 1919994, 2241118, 2562242, 2883366, 3204490, 3525614, 3846738, 4095766, 4430240, 4624572, 5131169, 5466538, 5802660, 5992856, 6481831, 6819357, 7160950, 7499335, 7838400]
    test_list = [314374, 635498, 956622]
    target_parcels = ParcelHistorical.objects.filter(id__in=test_list)

    return render(request, "parcel_main2.html", {"page_title": page_title,
                                                 "lat_input": lat,
                                                 "lon_input": lon,
                                                 "all_parcel_data": target_parcels})


class ParcelHistoryView(SingleTableView):
    model = Parcel
    table_class = ParcelHistoryTable
    template_name = "parcel_main.html"


def debug(request, parcel_id, subsection_id):
    section = RaleighSubsection.objects.get(id=subsection_id)
    parcel = ParcelHistorical.objects.get(id=parcel_id)

    # parcel_cleaned_geojson = parcel.data_geojson["geometry"]
    parcel_cleaned_geojson = json.dumps(parcel.data_geojson["geometry"])

    return render(request, "debug.html", {"section": section,
                                          "parcel": parcel,
                                          "parcel_cleaned_geojson": parcel_cleaned_geojson})


def raleigh_map(request):
    sections = serialize("geojson", RaleighSubsection.objects.all(), geometry_field="geom", fields=["pk"])

    geojson_data = '{"crs": {"properties": {"name": "EPSG:4326"}, "type": "name"}, "features": [], "type": "FeatureCollection"}'
    geojson_obj = json.loads(geojson_data)
    # orphan_parcels = ParcelHistorical.objects.filter(raleighsubsection__isnull=True)
    # paginator = Paginator(orphan_parcels, 100)
    # first_page = paginator.page(1)
    # first_page_list = first_page.object_list
    # parcel_list = []

    # for parcel in first_page_list:
    #     geojson_obj['features'].append(parcel.data_geojson)
    #     parcel_list.append(parcel.id)

    # parcel_list = [117423, 143664, 143666, 143667, 143668, 143669, 143670, 143671, 143673, 143675, 143676, 143682,
    #                143686, 143689, 143690, 143701, 143703, 143704, 143708, 143718, 143722, 143725, 143727, 143728,
    #                143729, 143730, 143739, 143742, 143746, 143748, 143749, 143752, 143758, 143759, 143761, 143762,
    #                143765, 143766, 143767, 143769, 143770, 143772, 143777, 143780, 143781, 143783, 143786, 143790,
    #                143792, 143795, 143797, 143799, 143804, 143805, 143806, 143810, 143814, 143823, 143824, 143826,
    #                143829, 143833, 143836, 143837, 143838, 143849, 143852, 143853, 143854, 143856, 143857, 143858,
    #                143861, 143863, 143865, 143867, 143875, 143878, 143879, 143881, 143882, 143883, 143892, 143900,
    #                143902, 143904, 143907, 143908, 143910, 143914, 143915, 143919, 143920, 143922, 143923, 143925,
    #                143930, 143935, 143943, 143960]
    parcel_list = [117423]
    first_page_list = []

    for parcel_id in parcel_list:
        parcel = ParcelHistorical.objects.get(id=parcel_id)
        first_page_list.append(parcel)

        # Add id info
        parcel.data_geojson["properties"]["PARCEL_ID"] = parcel.id
        geojson_obj['features'].append(parcel.data_geojson)

    geojson_data = json.dumps(geojson_obj)

    return render(request, "section_map.html", {"sections": sections,
                                                "geojson_data": geojson_data,
                                                "parcel_debug_data": first_page_list,
                                                "parcel_list": parcel_list})
