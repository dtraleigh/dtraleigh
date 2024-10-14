from django.core.management.base import BaseCommand
from transit.models import ShapefileRoute


def change_route_color(shapefile_route_id, new_color):
    try:
        # Validate new_color is one of the predefined choices
        if new_color not in dict(ShapefileRoute.COLORS):
            raise ValueError(f"{new_color} is not a valid color choice.")

        shapefile_route = ShapefileRoute.objects.get(id=shapefile_route_id)
        shapefile_route.route_color = new_color
        shapefile_route.save()

        print(f"Updated route color to {new_color} for ShapefileRoute ID {shapefile_route_id}.")

    except ShapefileRoute.DoesNotExist:
        print(f"ShapefileRoute with ID {shapefile_route_id} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")


class Command(BaseCommand):
    help = "Sets the ShapefileRoute instance colors to their defaults"

    def handle(self, *args, **options):
        red_routes = ["1 Capital", "4 Rex Hospital", "7 South Saunders", "7L Carolina Pines", "15 WakeMed",
                      "15L Trawick", "17 Rock Quarry", "24L North Crosstown", "36 Creedmoor"]
        blue_routes = ["2 Falls of Neuse", "9 Hillsborough", "16 Oberlin", "19 Apollo Heights", "20 Garner",
                       "26 Edwards Mill"]
        orange_routes = ["3 Glascock", "5 Biltmore Hills", "6 Crabtree", "12 Method", "18 Poole/Barwell",
                         "18S Poole", "Wake Forest Loop"]
        purple_routes = ["8 Six Forks", "11 Avent Ferry", "11L Buck Jones", "21 Caraleigh", "25L Triangle Town Center",
                         "33 Knightdale", "40X Wake Tech Express", "55X Poole Road Express", "70X Brier Creek Express"]
        magenta_routes = ["10 Longview", "23L Millbrook", "27 Blue Ridge"]
        green_routes = ["FRX", "WRX", "ZWX"]
        white_routes = ["R-Line"]

        for route in red_routes:
            for route_subset in ShapefileRoute.objects.filter(line_name__contains=route):
                change_route_color(route_subset.id, ShapefileRoute.RED)

        for route in blue_routes:
            for route_subset in ShapefileRoute.objects.filter(line_name__contains=route):
                change_route_color(route_subset.id, ShapefileRoute.BLUE)

        for route in orange_routes:
            for route_subset in ShapefileRoute.objects.filter(line_name__contains=route):
                change_route_color(route_subset.id, ShapefileRoute.ORANGE)

        for route in purple_routes:
            for route_subset in ShapefileRoute.objects.filter(line_name__contains=route):
                change_route_color(route_subset.id, ShapefileRoute.PURPLE)

        for route in magenta_routes:
            for route_subset in ShapefileRoute.objects.filter(line_name__contains=route):
                change_route_color(route_subset.id, ShapefileRoute.MAGENTA)

        for route in green_routes:
            for route_subset in ShapefileRoute.objects.filter(line_name__contains=route):
                change_route_color(route_subset.id, ShapefileRoute.GREEN)

        for route in white_routes:
            for route_subset in ShapefileRoute.objects.filter(line_name__contains=route):
                change_route_color(route_subset.id, ShapefileRoute.WHITE)
