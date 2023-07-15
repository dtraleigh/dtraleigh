from operator import itemgetter
from datetime import datetime, timedelta

from django.shortcuts import render
from django.core.serializers import serialize
from rpd.models import *
from django.views.decorators.clickjacking import xframe_options_exempt
from django.db.models import Q

from rpd.functions import is_glenwood_south

crime_categories = (
    "ASSAULT",
    "UNAUTHORIZED MOTOR VEHICLE USE",
    "VANDALISM",
    "ALL OTHER OFFENSES",
    "ROBBERY",
    "MV THEFT",
    "KIDNAPPING",
    "HUMAN TRAFFICKING",
    "DISORDERLY CONDUCT",
    "OBSCENE MATERIAL",
    "STOLEN PROPERTY",
    "HUMANE",
    "EXTORTION",
    "MURDER",
    "TRAFFIC",
    "FRAUD",
    "BURGLARY/RESIDENTIAL",
    "BURGLARY/COMMERCIAL",
    "PROSTITUTION",
    "SEX OFFENSES",
    "MISCELLANEOUS",
    "EMBEZZLEMENT",
    "WEAPONS VIOLATION",
    "DRUGS",
    "ARSON",
    "LARCENY",
    "LARCENY FROM MV",
    "DRUG VIOLATIONS",
    "BRIBERY",
    "LIQUOR LAW VIOLATIONS",
    "JUVENILE"
)

top_crime_categories = ("ASSAULT", "ALL OTHER OFFENSES", "WEAPONS VIOLATION",
                        "DRUGS", "DRUG VIOLATIONS", "LARCENY", "VANDALISM")


@xframe_options_exempt
def glenwood_map(request):
    glenwood_data = serialize("geojson", TrackArea.objects.all(), geometry_field="geom", fields=("long_name",))

    return render(request, "glenwood_map.html", {"glenwood_data": glenwood_data})


def glenwood(request):
    # confirmed that any incident with reported_block_address="" has no lat, long info
    yesterday_dt = datetime.today() - timedelta(days=1)
    yesterday = f"{yesterday_dt.strftime('%b')} {yesterday_dt.day}, {yesterday_dt.year}"
    gs_incidents_full_years = Incident.objects.filter(
        Q(reported_year__gt=2014), Q(reported_year__lt=datetime.today().year), Q(is_glenwood_south=True))
    gs_incidents_ytd = Incident.objects.filter(Q(reported_year__gt=2014), Q(reported_month__lte=yesterday_dt.month),
                                               Q(reported_day__lte=yesterday_dt.day), Q(is_glenwood_south=True))

    full_years = [str(year) for year in range(2015, datetime.today().year)]
    ytd_years = [str(year) for year in range(2015, datetime.today().year + 1)]

    all_the_data, all_the_labels = get_all_data_incident_totals(full_years, gs_incidents_full_years)
    top_data, all_the_top_labels = get_all_top_data_incident_totals(full_years, gs_incidents_full_years)
    ytd_data, all_the_top_labels = get_all_top_data_incident_totals(ytd_years, gs_incidents_ytd)

    data_totals = [sum(x) for x in zip(*all_the_data)]
    top_data_totals = [sum(y) for y in zip(*top_data)]
    ytd_totals = [sum(z) for z in zip(*ytd_data)]

    for rowA, cat1 in zip(all_the_data, all_the_labels):
        rowA.insert(0, cat1)
    for rowB, cat2 in zip(top_data, all_the_top_labels):
        rowB.insert(0, cat2)
    for rowC, cat3 in zip(ytd_data, all_the_top_labels):
        rowC.insert(0, cat3)

    # sort them in descending order by the most recent year's values
    all_the_data = sorted(all_the_data, key=itemgetter(-1), reverse=True)
    top_data = sorted(top_data, key=itemgetter(-1), reverse=True)
    ytd_data = sorted(ytd_data, key=itemgetter(-1), reverse=True)

    return render(request, "glenwood.html", {"years": full_years,
                                             "all_the_data": all_the_data,
                                             "data_totals": data_totals,
                                             "top_data": top_data,
                                             "top_data_totals": top_data_totals,
                                             "ytd_data": ytd_data,
                                             "ytd_years": ytd_years,
                                             "ytd_totals": ytd_totals,
                                             "yesterday": yesterday})


def glenwood_test(request):
    # confirmed that any incident with reported_block_address="" has no lat, long info
    yesterday_dt = datetime.today() - timedelta(days=1)
    yesterday = f"{yesterday_dt.strftime('%b')} {yesterday_dt.day}, {yesterday_dt.year}"
    gs_incidents_full_years = Incident.objects.filter(
        Q(reported_year__gt=2014), Q(reported_year__lt=datetime.today().year), Q(is_glenwood_south=True))
    gs_incidents_ytd = Incident.objects.filter(Q(reported_year__gt=2014), Q(reported_month__lte=yesterday_dt.month),
                                               Q(reported_day__lte=yesterday_dt.day), Q(is_glenwood_south=True))

    full_years = [str(year) for year in range(2015, datetime.today().year)]
    ytd_years = [str(year) for year in range(2015, datetime.today().year + 1)]

    all_the_data, all_the_labels = get_all_data_incident_totals(full_years, gs_incidents_full_years)
    top_data, all_the_top_labels = get_all_top_data_incident_totals(full_years, gs_incidents_full_years)
    ytd_data, all_the_top_labels = get_all_top_data_incident_totals(ytd_years, gs_incidents_ytd)

    data_totals = [sum(x) for x in zip(*all_the_data)]
    top_data_totals = [sum(y) for y in zip(*top_data)]
    ytd_totals = [sum(z) for z in zip(*ytd_data)]

    for rowA, cat1 in zip(all_the_data, all_the_labels):
        rowA.insert(0, cat1)
    for rowB, cat2 in zip(top_data, all_the_top_labels):
        rowB.insert(0, cat2)
    for rowC, cat3 in zip(ytd_data, all_the_top_labels):
        rowC.insert(0, cat3)

    # sort them in descending order by the most recent year's values
    all_the_data = sorted(all_the_data, key=itemgetter(-1), reverse=True)
    top_data = sorted(top_data, key=itemgetter(-1), reverse=True)
    ytd_data = sorted(ytd_data, key=itemgetter(-1), reverse=True)

    return render(request, "glenwood_debug.html", {"years": full_years,
                                                   "all_the_data": all_the_data,
                                                   "data_totals": data_totals,
                                                   "top_data": top_data,
                                                   "top_data_totals": top_data_totals,
                                                   "ytd_data": ytd_data,
                                                   "ytd_years": ytd_years,
                                                   "ytd_totals": ytd_totals,
                                                   "yesterday": yesterday})


def get_ytd_data(years, incidents):
    pass


def get_all_data_incident_totals(years, dt_incidents):
    all_the_data = []
    all_the_labels = []

    for crime_category in crime_categories:
        # create a list like ["2015_sum", "2016_sum", .... ]
        crime_category_list = [0 for _ in years]
        all_the_labels.append(crime_category)
        for incident in dt_incidents:
            if incident.crime_category == crime_category:
                position = incident.reported_year - 2015
                crime_category_list[position] += 1

        all_the_data.append(crime_category_list)

    return all_the_data, all_the_labels


def get_all_top_data_incident_totals(years, dt_incidents):
    top_data = []
    all_the_top_labels = []

    for top_crime_category in top_crime_categories:
        # create a list like ["2015_sum", "2016_sum", .... ]
        crime_category_list = [0 for _ in years]
        all_the_top_labels.append(top_crime_category)
        for incident in dt_incidents:
            if incident.crime_category == top_crime_category:
                position = incident.reported_year - 2015
                crime_category_list[position] += 1

        top_data.append(crime_category_list)

    return top_data, all_the_top_labels
