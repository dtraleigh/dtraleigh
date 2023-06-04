"""This is used to update all buildings in the database and add the LAND_VAL value

See: https://data-wake.opendata.arcgis.com/datasets/Wake::parcels/api
"""
from django.core.management.base import BaseCommand
from buildings.models import Building
from django.core.serializers import serialize


class Command(BaseCommand):
    def handle(self, *args, **options):
        # print_stats()
        create_geojson()
        # calculate_land_value_per_deed_acres()


def calculate_land_value_per_deed_acres():
    all_bldgs_for_map = Building.objects.filter(LAND_VAL__gt=0, DEED_ACRES__gt=0)
    length = len(all_bldgs_for_map)
    for count, bldg in enumerate(all_bldgs_for_map):
        bldg.LAND_VAL_per_DEED_ACRES = bldg.LAND_VAL / bldg.DEED_ACRES
        bldg.save()
        print(f"{count}/{length}")
        count += 1


def create_geojson():
    all_bldgs_for_map = Building.objects.filter(LAND_VAL__gt=0, DEED_ACRES__gt=0)
    output_geojson = serialize("geojson", all_bldgs_for_map,
                               geometry_field="geom",
                               fields=("LAND_VAL_per_DEED_ACRES",))

    with open("buildings/geojson_files/all_bldgs_land_value_deed_acres.json", "w") as f:
        f.write(output_geojson)


def find_percentile(bldgs, percentile):
    N = len(bldgs)
    sorted_bldgs = sorted(bldgs)
    n_index = ((percentile / 100) * N) - 1
    n_index = round(n_index)
    n_element = sorted_bldgs[n_index]
    return n_element


def print_stats():
    all_bldgs = Building.objects.all()
    count_land_val_none = 0
    count_land_val_zero = 0
    count_land_val_pos = 0
    land_val_values = []

    for bldg in all_bldgs:
        if bldg.LAND_VAL is None:
            count_land_val_none += 1
        elif bldg.LAND_VAL == 0:
            count_land_val_zero += 1
        else:
            count_land_val_pos += 1
        land_val_values.append(bldg.LAND_VAL)

    print(f"count_land_val_none: {count_land_val_none}")
    print(f"count_land_val_zero: {count_land_val_zero}")
    print(f"count_land_val_pos: {count_land_val_pos}\n")

    bldg_land_values = list(set(land_val_values))
    bldg_land_values = list(filter(None, bldg_land_values))  # Remove 0 and None
    # bldg_land_values = [x for x in bldg_land_values if x is not None]
    bldgs_per50 = find_percentile(bldg_land_values, 50)
    bldgs_per75 = find_percentile(bldg_land_values, 75)
    bldgs_per95 = find_percentile(bldg_land_values, 95)
    print(f"50th Percentile: {bldgs_per50}")
    print(f"75th Percentile: {bldgs_per75}")
    print(f"95th Percentile: {bldgs_per95}\n")

    # Get bldgs with:
    #   * a non-zero value for LAND_VAL
    #   * a non-zero value for DEED_ACRES
    valid_parcels = Building.objects.filter(LAND_VAL__gt=0, DEED_ACRES__gt=0)

    count_acres_none = 0
    count_acres_zero = 0
    count_acres_pos = 0
    acres_values = []

    for bldg in all_bldgs:
        if bldg.DEED_ACRES is None:
            count_acres_none += 1
        elif bldg.DEED_ACRES == 0:  # Check 0.0
            count_acres_zero += 1
        else:
            count_acres_pos += 1
        acres_values.append(bldg.DEED_ACRES)

    print(f"count_acres_none: {count_acres_none}")
    print(f"count_acres_zero: {count_acres_zero}")
    print(f"count_acres_pos: {count_acres_pos}\n")

    bldg_land_value_per_acre = [round(x.LAND_VAL / x.DEED_ACRES, 2) for x in valid_parcels]
    val_per_acre_per50 = find_percentile(bldg_land_value_per_acre, 50)
    val_per_acre_per75 = find_percentile(bldg_land_value_per_acre, 75)
    val_per_acre_per95 = find_percentile(bldg_land_value_per_acre, 95)
    print(f"50th Percentile: {val_per_acre_per50}")
    print(f"75th Percentile: {val_per_acre_per75}")
    print(f"95th Percentile: {val_per_acre_per95}\n")
