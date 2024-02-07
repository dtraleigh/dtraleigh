import logging
import requests
import geopy
import re
from datetime import datetime
from geopy.geocoders import Nominatim
# from geopy.extra.rate_limiter import RateLimiter

from django.contrib.gis.geos import Point
from develop.models import *
from develop.management.commands.emails import *

logger = logging.getLogger("django")


def get_itb_items(items_that_changed):
    tracked_items = []

    for item in items_that_changed:
        # For zoning requests, we want only the ones that are itb
        # NMs now have pins
        if isinstance(item, Zoning):
            try:
                lat, lon = get_lat_lon_by_pin(get_pins_from_location_url(item.location_url)[0])
                if is_itb(lat, lon):
                    tracked_items.append(item)
            except TypeError:
                logger.info(item)
                continue

        elif isinstance(item, NeighborhoodMeeting):
            try:
                lat, lon = get_lat_lon_by_pin(get_pins_from_location_url(item.rezoning_site_address_url)[0])
                if is_itb(lat, lon):
                    tracked_items.append(item)
            except TypeError:
                logger.info(item)
                continue

        # Dev plans, we can calculate is_itb using geom x and y
        elif isinstance(item, DevelopmentPlan):
            if is_itb(item.geom.y, item.geom.x):
                tracked_items.append(item)

        # Text change cases, neighborhood meetings aren't always location specific so just add all of them
        elif isinstance(item, TextChangeCase):
            tracked_items.append(item)

        # elif isinstance(item, NeighborhoodMeeting):
        #     if item.is_itb_override:
        #         tracked_items.append(item)
        #         continue
        #     project_name_parts = split_up_project_name(item.rezoning_site_address)
        #     for piece in project_name_parts:
        #         address_lat, address_lon = get_lat_lon_by_address(piece)
        #         if address_lat and address_lon:
        #             # If anything hits True, add it and break
        #             if is_itb(address_lat, address_lon):
        #                 tracked_items.append(item)
        #                 break
        else:
            project_name_parts = split_up_project_name(item.project_name)
            for piece in project_name_parts:
                try:
                    address_lat, address_lon = get_lat_lon_by_address(piece)
                except TypeError as e:
                    message = f"{e}\n"
                    message += f"piece: {piece}\n"
                    message += f"item.project_name: {item.project_name}\n"
                    logger.info(message)
                    send_email_notice(message, email_admins())
                if address_lat and address_lon:
                    # If anything hits True, add it.
                    if is_itb(address_lat, address_lon):
                        tracked_items.append(item)

    return tracked_items


def clean_address(address):
    """
    We need to clean the addresses a bit.
    Scenario 1: "S West St" needs to be "South West St"
    Scenario 2: "200 S West St" needs to be "200 South west St"
    Scenario 3: Need to add city, state, and country
    """
    address_parts = address.split()

    # There are a couple exceptions
    # "T W ALEXANDER  DR"
    # "M E Valentine Dr"
    # Also, one word places, such as 'Chick-Fil-A' don't work so will just ignore them in an ugly way.
    if len(address_parts) > 1:
        if not address_parts[0].lower() == "t" and not address_parts[1].lower() == "w" and \
                not address_parts[0].lower() == "m" and not address_parts[1].lower() == "e":
            for i, part in enumerate(address_parts):
                if part.lower() == "s":
                    address_parts[i] = "south"
                elif part.lower() == "n":
                    address_parts[i] = "north"
                elif part.lower() == "w":
                    address_parts[i] = "west"
                elif part.lower() == "e":
                    address_parts[i] = "east"
    else:
        return None

    return " ".join(address_parts) + ", raleigh NC USA"


def get_wake_location(lat, lon):
    """
    Take in a lat and lon and check which muni it is in
    """
    pnt = Point(lon, lat)
    try:
        return WakeCorporate.objects.get(geom__intersects=pnt)
    except Exception as e:
        logger.info(e)
        return None


def is_itb(lat, lon):
    """
    Take in a lat and lon (ints) and return True if the point is inside the
    ITB Raleigh TrackArea
    """
    pnt = Point(lon, lat)
    itb = TrackArea.objects.get(short_name="ITB")

    try:
        if TrackArea.objects.get(geom__intersects=pnt) == itb:
            return True
    except TrackArea.DoesNotExist:
        return False


def get_lat_lon_by_pin(pin):
    """This uses the County's address point API and given a pin, we return the x (lon) and y (lat) coordinates"""
    if pin:
        url = f"http://maps.wakegov.com/arcgis/rest/services/Property/Addresses/MapServer/0/query?where=PIN_NUM={str(pin)}&outFields=*&outSR=4326&f=json"
    else:
        return None, None

    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)

    if response.status_code == 200:
        try:
            if response.json()["features"]:
                coordinates = response.json()["features"][0]["geometry"]
                return coordinates["y"], coordinates["x"]
            else:
                return None, None
        except IndexError:
            message = "IndexError in location.get_lat_lon_by_pin()\n"
            message += str(response.text.encode('utf8'))
            send_email_notice(message, email_admins())
            return None, None
        except KeyError:
            message = "KeyError in location.get_lat_lon_by_pin()\n"
            message += str(response.text.encode('utf8'))
            send_email_notice(message, email_admins())
            return None, None

    return None, None


def get_parcel_by_pin(pin):
    """This function will use a pin and return the parcel information that comes from the county's parcel endpoint"""
    url = f"http://maps.wakegov.com/arcgis/rest/services/Property/Addresses/MapServer/0/query?where=PIN_NUM={pin}&outFields=*&outSR=4326&f=json"

    response = requests.request("GET", url, headers={}, data={})

    if response.status_code == 200:
        try:
            return response.json()["features"][0]["attributes"]
        except KeyError as e:
            print(e)
            print(response.json())
    return response


def get_pins_from_location_url(location_url):
    """This function takes in a location_url. We use the location_url string, extract the pins, and return them."""
    if location_url:
        try:
            return location_url.replace(" ", "").split("=")[1].split(",")
        except IndexError:
            message = location_url
            message += "\nlocation.get_pins_from_location_url: This url does not have pins"
            send_email_notice(message, email_admins())
            return None
    else:
        return None


def split_up_project_name(project_name):
    """
    Take in a project name return it, split into parts. So far, split up by "/" and ","
    """
    text_parts_slash = project_name.split("/")
    text_parts_comma = re.split(r',|\(', project_name)

    # Special case: Path for Bloc 83 SR
    if project_name == "BLOC83 Tower 3615 W Morgan St":
        return ["615 West Morgan Street"]
    if len(text_parts_slash) == 1:
        return text_parts_comma
    elif len(text_parts_slash) > 1:
        return text_parts_slash


def get_lat_lon_by_address(scraped_address):
    """Take in a string and return a lat, lon value"""
    geolocator = Nominatim(user_agent="leo@dtraleigh.com")

    if scraped_address:
        address = clean_address(scraped_address)  # this will append " raleigh NC USA"
        try:
            n = datetime.now().strftime("%H:%M %m-%d-%y")
            location = geolocator.geocode(address)
        except geopy.exc.GeocoderTimedOut:
            logger.info(
                f"{n}: location.get_lat_lon_by_address - Exception thrown geopy.exc.GeocoderTimedOut. Address: {address}")
            return None
        except geopy.adapters.AdapterHTTPError:
            logger.info(
                f"{n}: location.get_lat_lon_by_address - Exception thrown geopy.adapters.AdapterHTTPError. Address: {address}")
            return None
        except geopy.exc.GeocoderServiceError:
            logger.info(
                f"{n}: location.get_lat_lon_by_address - Exception thrown geopy.exc.GeocoderServiceError 502 Error. Address: {address}")
            return None

        if location:
            return location.latitude, location.longitude
        else:
            return None, None

    return None
