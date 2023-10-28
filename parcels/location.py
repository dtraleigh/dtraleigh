from django.contrib.gis.geos import Point
from parcels.models import Parcel


def get_parcels_from_point(lat, lon):
    """
    Take in a lat and lon (floats) and return all parcels where the point is inside
    the geometry
    """
    pnt = Point(lon, lat)

    return Parcel.objects.filter(geom__intersects=pnt)
