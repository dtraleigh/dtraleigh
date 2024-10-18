from django.core.management.base import BaseCommand
from transit.models import ShapefileRoute

# Predefined list of 40 colors
PREDEFINED_COLORS = [
    "#FF5733", "#33FF57", "#3357FF", "#F1C40F", "#9B59B6", "#E74C3C", "#1ABC9C", "#3498DB",
    "#2ECC71", "#F39C12", "#8E44AD", "#2C3E50", "#27AE60", "#D35400", "#C0392B", "#2980B9",
    "#16A085", "#E67E22", "#34495E", "#D0ECE7", "#82E0AA", "#F7DC6F", "#AF7AC5", "#EC7063",
    "#73C6B6", "#5499C7", "#FAD7A0", "#5DADE2", "#48C9B0", "#52BE80", "#7DCEA0", "#F0B27A",
    "#F1948A", "#D5F5E3", "#D7BDE2", "#A3E4D7", "#A9CCE3", "#F9E79F", "#F5CBA7", "#D98880"
]


def change_route_color(route_instances, new_color):
    try:
        for route in route_instances:
            route.route_color = new_color
            route.save()
        print(
            f"Updated route color to {new_color} for {route_instances.count()} ShapefileRoute(s) with line_name {route_instances.first().line_name}.")
    except Exception as e:
        print(f"An error occurred: {e}")


class Command(BaseCommand):
    help = "Sets unique colors for each ShapefileRoute instance, grouping by line_name"

    def handle(self, *args, **options):
        # Group routes by line_name
        line_names = ShapefileRoute.objects.values_list('line_name', flat=True).distinct()
        num_routes = len(line_names)

        if num_routes > len(PREDEFINED_COLORS):
            print(
                f"Warning: There are more routes ({num_routes}) than available colors ({len(PREDEFINED_COLORS)}). Colors will be reused.")

        # Assign colors to routes with the same line_name
        for i, line_name in enumerate(line_names):
            route_instances = ShapefileRoute.objects.filter(line_name=line_name, is_enabled=True)
            if route_instances.exists():
                # Use modulus to cycle through the predefined colors if there are more routes than colors
                color = PREDEFINED_COLORS[i % len(PREDEFINED_COLORS)]
                change_route_color(route_instances, color)
