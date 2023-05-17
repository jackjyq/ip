import json
import logging
import os
import sys
from typing import Dict
import sh
import geoip2.database
from geoip2.errors import AddressNotFoundError
from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest
from django.core.management import execute_from_command_line
from django.core.wsgi import get_wsgi_application
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import path
from geopy.geocoders import Nominatim
from user_agents import parse
from whitenoise import WhiteNoise
from file_read_backwards import FileReadBackwards
from ip2Region import Ip2Region
import datetime

# Django server settings
BASE_DIR = os.path.dirname(__file__)
DEBUG = os.environ.get("DEBUG", False) == "True"
SECRET_KEY = os.environ.get("SECRET_KEY", os.urandom(32))


settings.configure(
    DEBUG=DEBUG,
    SECRET_KEY=SECRET_KEY,
    ROOT_URLCONF=__name__,
    ALLOWED_HOSTS=["*"],
    MIDDLEWARE_CLASSES=(
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
    ),
    INSTALLED_APPS=("django.contrib.staticfiles",),
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [
                os.path.join(BASE_DIR, "templates/"),
            ],
        },
    ],
    STATICFILES_DIRS=(os.path.join(BASE_DIR, "static/"),),
    STATIC_URL="/static/",
)

# logger settings
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

handler = logging.FileHandler("django.log")
handler.setLevel(logging.INFO)
handler.setFormatter(formatter)
logger.addHandler(handler)

console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
logger.addHandler(console)


# Other services initialization
# https://github.com/lionsoul2014/ip2region
ip2region_reader = Ip2Region("./ip_data/ip2region/ip2region.db")
# https://geoip2.readthedocs.io/en/latest/
geolite2_reader = geoip2.database.Reader("./ip_data/GeoLite2/GeoLite2-City.mmdb")
# https://geopy.readthedocs.io/en/stable/
geolocator = Nominatim(user_agent="ip.jackjyq.com")


def get_index(request: WSGIRequest) -> HttpResponse:
    ip_address: str = get_ip_address(request)
    ip_location: Dict = get_ip_location(ip_address)
    user_agent: Dict = get_user_agent(request)
    accept_language: Dict = {
        "accept_language": request.META.get("HTTP_ACCEPT_LANGUAGE")
    }
    response: Dict = ip_location | user_agent | accept_language

    def get_text_response(d: dict) -> str:
        s = ""
        for key in d.keys():
            s += key + ": " + str(d[key]) + "\r\n"
        return s

    if request.content_type == "application/json" or "json" in request.path:
        logger.info(f"API: {json.dumps(response, ensure_ascii=False, sort_keys=True)}")
        return JsonResponse(
            response,
            json_dumps_params={"ensure_ascii": False, "indent": 2},
        )
    elif user_agent["user_agent"].startswith("curl") or "text" in request.path:
        logger.info(f"TEXT: {json.dumps(response, ensure_ascii=False, sort_keys=True)}")
        return HttpResponse(get_text_response(response), content_type="text/plain")
    else:
        logger.info(f"Web: {json.dumps(response, ensure_ascii=False, sort_keys=True)}")
        return render(
            request,
            "index.html",
            response | {"visits": get_number_visits(datetime.timedelta(days=1))},
        )


def get_ip_address(request: WSGIRequest) -> str:
    """to get the client ip address even if behind nginx

    Returns:
        "0.0.0.0" if not found
    Refs:
      s  https://stackoverflow.com/a/5976065
    """
    if x_forwarded_for := request.META.get("HTTP_X_FORWARDED_FOR"):
        ip_address = x_forwarded_for.split(",")[-1].strip()
    else:
        ip_address = request.META.get("REMOTE_ADDR", "0.0.0.0")
    return ip_address


def get_user_agent(request: WSGIRequest) -> Dict:
    """to get the user agent information as a dictionary

    ref: https://github.com/selwin/python-user-agents
    """
    ua_string = request.META.get("HTTP_USER_AGENT")
    user_agent = parse(ua_string)
    return {
        "user_agent": ua_string,
        "browser": user_agent.get_browser(),
        "os": user_agent.get_os(),
        "device": user_agent.get_device(),
    }


def get_number_visits(times: datetime.timedelta) -> int:
    """get the number of visits from log file

    Returns:
        number of visits in the past times
    """
    number_visits = 0
    with FileReadBackwards("./django.log", encoding="utf-8") as frb:
        # getting lines by lines starting from the last line up
        for line in frb:
            try:
                line_time = datetime.datetime.strptime(
                    line.split(" - ")[0], "%Y-%m-%d %H:%M:%S,%f"
                )
            except ValueError:
                continue
            if datetime.datetime.now() - line_time < times:
                number_visits += 1
            else:
                break
    return number_visits


def get_ip_location(ip_address: str) -> Dict:
    """query the ip location

    None when the field is unknown
    """
    # use ip2region database to get the country name
    ip2region_result = (
        ip2region_reader.btreeSearch(ip_address)["region"].decode().split("|")
    )
    ip2region_result = [None if _ == "0" else _ for _ in ip2region_result]
    ip2region_location = {
        "ip": ip_address,
        "country": ip2region_result[0],
        "region": ip2region_result[1],
        "province": ip2region_result[2],
        "city": ip2region_result[3],
        "isp": ip2region_result[4],
        "database_name": "ip2region",
        "database_href": "https://gitee.com/lionsoul/ip2region/",
    }
    # try GeoLite2 database for ip address that is not in China
    if ip2region_location["country"] != "中国":
        try:
            geolite2_result = geolite2_reader.city(ip_address)
            geolite2_location = {
                "ip": ip_address,
                "country": geolite2_result.country.names.get(
                    "zh-CN", geolite2_result.country.name
                ),
                "region": None,
                "province": geolite2_result.subdivisions.most_specific.names.get(
                    "zh-CN", geolite2_result.subdivisions.most_specific.name
                ),
                "city": geolite2_result.city.names.get(
                    "zh-CN", geolite2_result.city.name
                ),
                "isp": None,
                "database_name": "GeoLite2",
                "database_href": "https://www.maxmind.com/",
            }
            return geolite2_location
        except AddressNotFoundError:
            pass
    # otherwise, fall back to use ip2region database
    return ip2region_location


def get_address_from_coordinates(request: WSGIRequest) -> JsonResponse:
    """get address from coordinates

    Returns:
        str: {"address": location.address}
    """
    latitude = request.GET.get("latitude")
    longitude = request.GET.get("longitude")
    try:
        location = geolocator.reverse(f"{latitude}, {longitude}", language="zh-cn")
    except ValueError:
        return JsonResponse({"address": None})
    if not location:
        return JsonResponse({"address": None})
    return JsonResponse({"address": location.address})


def get_headers(request: WSGIRequest) -> HttpResponse:
    headers = {}
    for attribute in sorted(dict(request.headers.items())):
        headers[attribute] = request.headers[attribute]
    return render(
        request,
        "headers.html",
        context={"headers": headers},
    )


def get_navigator(request: WSGIRequest) -> HttpResponse:
    return render(
        request,
        "navigator.html",
    )


def get_whois(request: WSGIRequest) -> HttpResponse:
    ip = get_ip_address(request)
    whois = sh.Command("/usr/bin/whois")
    whois_info = whois(ip)
    if not whois_info:
        whois_info = "No whois information found."
    return render(
        request,
        "whois.html",
        context={"whois": [line.split(": ", 2) for line in whois_info.splitlines()]},
    )


def get_more(request: WSGIRequest) -> HttpResponse:
    return render(
        request,
        "more.html",
    )


urlpatterns = [
    path("", get_index),
    path("json", get_index),
    path("text", get_index),
    path("address", get_address_from_coordinates),
    path("headers", get_headers),
    path("navigator", get_navigator),
    path("whois", get_whois),
    path("more", get_more),
]
application = get_wsgi_application()
application = WhiteNoise(application, root="./static", prefix="static/")

if __name__ == "__main__":
    execute_from_command_line(sys.argv)
