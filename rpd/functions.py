from rpd.models import *
from django.contrib.gis.geos import Point


def is_glenwood_south(incident):
    """
    Take in an incident and return true if this incident took place inside the
    glenwood south track area
    """
    glenwood_south = TrackArea.objects.get(short_name="glenwood")
    if incident.geom:
        pnt = incident.geom
    elif incident.latitude and incident.longitude:
        pnt = Point(incident.longitude, incident.latitude)
    else:
        return False

    try:
        if TrackArea.objects.get(geom__intersects=pnt) == glenwood_south:
            return True
    except TrackArea.DoesNotExist:
        return False
