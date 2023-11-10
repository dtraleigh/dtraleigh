import logging
from newBernTOD.functions import query_url_with_retries

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
