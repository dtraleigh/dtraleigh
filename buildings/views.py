from django.shortcuts import render
from django.views.decorators.clickjacking import xframe_options_exempt
from django.core.serializers import serialize
from buildings.models import *
from django.contrib.gis.geos import MultiPolygon
from django.db.models import Q
from arcgis2geojson import arcgis2geojson
from buildings.management.commands.bldg_land_val_stats import find_percentile

def decades_to_show():
    return ["pre-1920s", "1920s", "1930s", "1940s", "1950s", "1960s",
            "1970s", "1980s", "1990s", "2000s", "2010s"]


def get_raleigh_borders_in_geojson():
    raleigh_borders = Border.objects.get(muni_name="raleigh")
    return raleigh_borders.border_geojson


@xframe_options_exempt
def building_date_map(request):
    try:
        bldg_data1 = Decade.objects.get(decade_name="pre-1920s").output_geojson_reduced
        bldg_data2 = Decade.objects.get(decade_name="1920s").output_geojson_reduced
        bldg_data3 = Decade.objects.get(decade_name="1930s").output_geojson_reduced
        bldg_data4 = Decade.objects.get(decade_name="1940s").output_geojson_reduced
        bldg_data5 = Decade.objects.get(decade_name="1950s").output_geojson_reduced
        bldg_data6 = Decade.objects.get(decade_name="1960s").output_geojson_reduced
        bldg_data7 = Decade.objects.get(decade_name="1970s").output_geojson_reduced
        bldg_data8 = Decade.objects.get(decade_name="1980s").output_geojson_reduced
        bldg_data9 = Decade.objects.get(decade_name="1990s").output_geojson_reduced
        bldg_data10 = Decade.objects.get(decade_name="2000s").output_geojson_reduced
        bldg_data11 = Decade.objects.get(decade_name="2010s").output_geojson_reduced
        bldg_data12 = Decade.objects.get(decade_name="2020s").output_geojson_reduced
    except Decade.DoesNotExist:
        bldg_data1 = None
        bldg_data2 = None
        bldg_data3 = None
        bldg_data4 = None
        bldg_data5 = None
        bldg_data6 = None
        bldg_data7 = None
        bldg_data8 = None
        bldg_data9 = None
        bldg_data10 = None
        bldg_data11 = None
        bldg_data12 = None

    raleigh_borders = get_raleigh_borders_in_geojson()

    return render(request, "buildings.html", {"bldg_data1": bldg_data1,
                                              "bldg_data2": bldg_data2,
                                              "bldg_data3": bldg_data3,
                                              "bldg_data4": bldg_data4,
                                              "bldg_data5": bldg_data5,
                                              "bldg_data6": bldg_data6,
                                              "bldg_data7": bldg_data7,
                                              "bldg_data8": bldg_data8,
                                              "bldg_data9": bldg_data9,
                                              "bldg_data10": bldg_data10,
                                              "bldg_data11": bldg_data11,
                                              "bldg_data12": bldg_data12,
                                              "raleigh_borders": raleigh_borders})


@xframe_options_exempt
def decade_map(request, decade):
    try:
        bldg_data = Decade.objects.get(decade_name=decade).output_geojson_reduced
    except Decade.DoesNotExist:
        bldg_data = None

    raleigh_borders = get_raleigh_borders_in_geojson()

    return render(request, "buildings.html", {"bldg_data": bldg_data,
                                              "raleigh_borders": raleigh_borders})


@xframe_options_exempt
def bar_chart(request):
    # decades_labels = decades_to_show()
    #
    # buildings_totals = []
    # for decade_label in decades_labels:
    #     decade = Decade.objects.get(decade_name=decade_label)
    #     bldg_amt = len(Building.objects.filter(Q(YEAR_BUILT__gte=decade.start_year), Q(YEAR_BUILT__lte=decade.end_year)))
    #     buildings_totals.append(bldg_amt)

    # return render(request, "barchart.html", {"decades_labels": decades_labels,
    #                                          "buildings_totals": buildings_totals})

    # Let's just hardcode it for now to save on compute
    return render(request, "barchart.html")


@xframe_options_exempt
def bar_chart2(request):
    # percent_labels = [x + 1 for x in range(100)]
    # percentile_values = []

    # Get bldgs with:
    #   * a non-zero value for LAND_VAL
    #   * a non-zero value for DEED_ACRES
    # valid_parcels = Building.objects.filter(LAND_VAL__gt=0, DEED_ACRES__gt=0)
    # bldg_land_value_per_acre = [y.LAND_VAL_per_DEED_ACRES for y in valid_parcels]

    # for percent in percent_labels:
    #     value = find_percentile(bldg_land_value_per_acre, percent)
    #     percentile_values.append(value)

    # return render(request, "lv_barchart.html", {"percent_labels": percent_labels,
    #                                             "percentile_values": percentile_values})

    # Let's just hardcode it for now to save on compute
    return render(request, "lv_barchart.html")


@xframe_options_exempt
def geojson_helper(request, decade):
    try:
        bldg_data = Decade.objects.get(decade_name=decade).output_geojson_reduced
    except Decade.DoesNotExist:
        bldg_data = None

    return render(request, "geojson.html", {"bldg_data": bldg_data})


@xframe_options_exempt
def land_value_test(request):
    lv_map_test = CustomMap.objects.get(id=2)

    return render(request, "lv_map.html", {"lv_map_test": lv_map_test.output_geojson})


@xframe_options_exempt
def land_value(request):
    lv_map = CustomMap.objects.get(map_name="Land Value per Acre Map")

    return render(request, "lv_map.html", {"lv_map_test": lv_map.output_geojson})
