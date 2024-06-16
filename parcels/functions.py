import logging

from django.contrib.gis.geos import Point

import parcels.models
from newBernTOD.functions import query_url_with_retries
from parcels.models import RaleighSubsection, Parcel, ParcelHistorical

logger = logging.getLogger("django")


def get_all_RAL_parcels(offset, count_only=False):
    url = f"https://maps.wake.gov/arcgis/rest/services/Property/Parcels/MapServer/0/query?where=CITY='RAL'&outFields" \
          f"=*&inSR=4326&spatialRel=esriSpatialRelIntersects&outSR=4326&f=json&" \
          f"returnCountOnly={str(count_only).lower()}&resultOffset={str(offset)}"

    response = query_url_with_retries(url)

    return response.json()


def get_freeman_parcels(offset, count_only=False):
    url = f"https://maps.wake.gov/arcgis/rest/services/Property/Parcels/MapServer/0/query?where=1%3D1&outFields" \
          f"=*&geometry=-78.625%2C35.776%2C-78.623%2C35.778&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel" \
          f"=esriSpatialRelIntersects&outSR=4326&f=json&returnCountOnly={str(count_only).lower()}" \
          f"&resultOffset={str(offset)}"

    response = query_url_with_retries(url)

    return response.json()


def get_ral_subsection(lat, lon):
    """
    Take in a lat and lon and return the subsection that it lands in
    """
    pnt = Point(lon, lat)
    try:
        subsection = RaleighSubsection.objects.get(geom__intersects=pnt)
        return subsection
    except parcels.models.RaleighSubsection.DoesNotExist as e:
        logger.info(e)
        logger.info(f"Failed to find a Raleigh subsection for {lat}, {lon}")
        return None


def get_parcels_from_point(lat, lon, subsection=None):
    """
    Take in a lat and lon (floats) and return all parcels where the point is inside
    the geometry.
    """
    pnt = Point(lon, lat)

    return Parcel.objects.filter(geom__intersects=pnt)


def get_parcel_historical_from_point(lat, lon, subsection=None):
    """
    Take in a lat and lon (floats) and return all historical parcels where the point is inside
    the geometry. Optional subsection argument.
    """
    if lat is None and lon is None:
        return []

    pnt = Point(lon, lat)

    if not subsection:
        subsection = get_ral_subsection(lat, lon)

    parcel_pool = subsection.sections.all()
    overlapping_parcels = []
    warning_parcels = []

    for parcel in parcel_pool:
        parcel_geom = parcel.get_geosgeom_object()
        if parcel_geom:
            if parcel_geom.intersects(pnt):
                overlapping_parcels.append(parcel)
        else:
            warning_parcels.append(parcel)

    if warning_parcels:
        print(f"WARNING: Some parcels did not have a geos geometry. {warning_parcels}")

    return overlapping_parcels
