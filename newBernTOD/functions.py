import requests
from django.contrib.gis.geos import GEOSGeometry


def get_geometry_by_parcel_pin(pin):
    url = f"https://maps.wakegov.com/arcgis/rest/services/Property/Parcels/MapServer/0/query?geometryType" \
          f"=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outSR=4326&f=json&outFields" \
          f"=*&where=PIN_NUM={pin}"

    response = requests.request("GET", url, headers={}, data={})

    if response.status_code == 200:
        try:
            parcel_geometry_json = response.json()["features"][0]["geometry"]
            return GEOSGeometry('{ "type": "Polygon", "coordinates": ' + str(parcel_geometry_json["rings"]) + ' }')
        except KeyError as e:
            print(e)
            print(response.json())
            return None
        except IndexError as e:
            print(e)
            print(f"Pin: {pin}")
            print(response.json())
    return None


def get_parcel_fields_by_pin(pin):
    url = f"https://maps.wakegov.com/arcgis/rest/services/Property/Parcels/MapServer/0/query?where=PIN_NUM={pin}"\
          f"&outSR=4326&f=json&returnGeometry=false&outFields=*"

    response = requests.request("GET", url, headers={}, data={})

    return response.json()
