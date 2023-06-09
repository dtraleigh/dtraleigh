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


def get_hod_general_overlays():
    url = "https://maps.raleighnc.gov/arcgis/rest/services/Planning/Overlays/MapServer/7/query?where=1%3D1&outFields" \
          "=*&outSR=4326&f=json"

    payload = {}
    headers = {
        'Cookie': 'AGS_ROLES="419jqfa+uOZgYod4xPOQ8Q=="'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    return response.json()


def get_hod_streetside_overlays():
    url = "https://maps.raleighnc.gov/arcgis/rest/services/Planning/Overlays/MapServer/8/query?outFields=*&where=1" \
          "%3D1&f=geojson"

    payload = {}
    headers = {
        'Cookie': 'AGS_ROLES="419jqfa+uOZgYod4xPOQ8Q=="'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    return response.json()


def get_ncod_overlays():
    url = "https://maps.raleighnc.gov/arcgis/rest/services/Planning/Overlays/MapServer/9/query?where=1%3D1&outFields=*&outSR=4326&f=json"

    payload = {}
    headers = {
        'Cookie': 'AGS_ROLES="419jqfa+uOZgYod4xPOQ8Q=="'
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    return response.json()


def get_parcels_around_new_bern(offset):
    url = f"https://maps.wake.gov/arcgis/rest/services/Property/Parcels/MapServer/0/query?where=1%3D1&outFields" \
          f"=*&geometry=-78.654%2C35.769%2C-78.580%2C35.793&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel" \
          f"=esriSpatialRelIntersects&outSR=4326&f=json&resultOffset={str(offset)}"

    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)

    return response.json()
