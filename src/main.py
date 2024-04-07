import datetime
import ipaddress
import json
import logging
import os
import socket
import sys
from glob import glob
from typing import Dict, Optional
from urllib.parse import urlparse

import geoip2.database
import sh
from cachetools.func import lru_cache, ttl_cache
from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest
from django.core.management import execute_from_command_line
from django.core.wsgi import get_wsgi_application
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import path
from django.views.decorators.http import require_http_methods
from django.views.generic.base import TemplateView
from file_read_backwards import FileReadBackwards
from geoip2.errors import AddressNotFoundError
from geopy.exc import GeocoderUnavailable
from geopy.geocoders import Nominatim
from user_agents import parse
from whitenoise import WhiteNoise
from xdbSearcher import XdbSearcher

# Django server settings
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DEBUG = os.environ.get("DEBUG", False) == "True"  # the environ return value is str
SECRET_KEY = os.environ.get("SECRET_KEY", os.urandom(32))
LOG_FILE = "./django.log"
IP2REGION_DB = os.path.join(BASE_DIR, "data/ip2region/ip2region.xdb")
GEOLITE2_DB = os.path.join(BASE_DIR, "data/GeoLite2/GeoLite2-City.mmdb")
WHOIS_FILE = "/usr/bin/whois"


def boot_up_check():
    # the size shall not be too small (< 1MB)
    if os.path.isfile(IP2REGION_DB) and os.path.getsize(IP2REGION_DB) > 1024 * 1024:
        print(f"{IP2REGION_DB} check... ✓")
    else:
        print(f"{IP2REGION_DB} check... x")
        sys.exit(1)
    if os.path.isfile(GEOLITE2_DB) and os.path.getsize(GEOLITE2_DB) > 1024 * 1024:
        print(f"{GEOLITE2_DB} check... ✓")
    else:
        print(f"{GEOLITE2_DB} check... x")
        sys.exit(1)
    if os.path.isfile(WHOIS_FILE):
        print(f"{WHOIS_FILE} check... ✓")
    else:
        print(f"{WHOIS_FILE} check... x")
        print("Run `sudo apt install whois` and try again")
        sys.exit(1)


boot_up_check()

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


def get_logger() -> logging.Logger:
    """NOTE: Do NOT rotate the log

    https://docs.python.org/3/library/logging.handlers.html#timedrotatingfilehandler
    https://docs.python.org/3/howto/logging-cookbook.html#logging-to-a-single-file-from-multiple-processes
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(level=logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    logger.addHandler(console)
    return logger


LOGGER = get_logger()


def get_number_visits_from_log(times: datetime.timedelta, log_file: str) -> int:
    """get the number of visits in ONE log file, without cache"""
    number_visits = 0
    with FileReadBackwards(log_file, encoding="utf-8") as frb:
        # getting line by line starting from the last line up
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


def get_number_visits(times: datetime.timedelta) -> int:
    """get the number of visits from ALL log files in the past `times`

    Returns:
        number of visits in the past times
    """
    number_visits = get_number_visits_from_log(times=times, log_file=LOG_FILE)

    # iterate log file in reverse chronological order
    for log_file in sorted(glob(f"{LOG_FILE}.*"), reverse=True):
        if (
            number_visits_of_current_log_file := get_number_visits_from_log(
                times=times, log_file=log_file
            )
        ) == 0:
            break
        else:
            number_visits += number_visits_of_current_log_file
    return number_visits


# Other services initialization
# https://github.com/lionsoul2014/ip2region
IP2REGION_READER = XdbSearcher(IP2REGION_DB)
# https://geoip2.readthedocs.io/en/latest/
GEOLITE2_READER = geoip2.database.Reader(GEOLITE2_DB)
# https://geopy.readthedocs.io/en/stable/
GEOLOCATOR = Nominatim(user_agent="ip.jackjyq.com")


def is_valid_ipv4(ip_address: str) -> bool:
    try:
        ipaddress.IPv4Address(ip_address)
        return True
    except ipaddress.AddressValueError:
        return False


@require_http_methods(["POST"])
def get_ips(request: WSGIRequest) -> JsonResponse:
    """get ips by POST API

    request body:
        {
            "ips": []
            "databases": choose from both, ip2region, GeoLite2
        }

    benchmark
    on macbook pro 2019
        - maxmind query speed: 1.5s per 10k request
        - ip2region query speed: 0.1s per 10k request
    """
    NUNMBER_OF_IPS = {
        "both": 666,
        "ip2region": 10000,
        "GeoLite2": 666,
    }
    if request.method != "POST":
        return JsonResponse({"error": "Only POST is allowed"}, status=405)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    if not isinstance(data, dict):
        return JsonResponse({"error": "POST body shall be a dict"}, status=400)
    if "ips" not in data:
        return JsonResponse({"error": "POST body shall contain 'ips'"}, status=400)
    if not isinstance(data["ips"], list):
        return JsonResponse({"error": "POST body['ips'] shall be a list"}, status=400)
    if not all(isinstance(ip, str) for ip in data["ips"]):
        return JsonResponse(
            {"error": "POST body['ips'] shall be a list of str"}, status=400
        )
    database = data.get("database", "both")
    if database not in ["both", "ip2region", "GeoLite2"]:
        database = "both"
    if len(data["ips"]) > NUNMBER_OF_IPS[database]:
        return JsonResponse(
            {"error": "POST body['ips'] for {database} be less than {NUNMBER_OF_IPS}"},
            status=400,
        )
    LOGGER.info(f"API: {json.dumps(data, ensure_ascii=False, sort_keys=True)}")
    return JsonResponse(
        {
            ip: get_ip_location(ip, database=database)
            for ip in data["ips"]
            if is_valid_ipv4(ip)
        },
        json_dumps_params={"ensure_ascii": False, "indent": 2},
    )


@require_http_methods(["GET"])
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
        LOGGER.info(f"API: {json.dumps(response, ensure_ascii=False, sort_keys=True)}")
        return JsonResponse(
            response,
            json_dumps_params={"ensure_ascii": False, "indent": 2},
        )
    elif (
        user_agent["user_agent"].startswith("curl")
        or "PowerShell" in user_agent["user_agent"]
        or "text" in request.path
    ):
        LOGGER.info(f"TEXT: {json.dumps(response, ensure_ascii=False, sort_keys=True)}")
        return HttpResponse(
            get_text_response(response),
            content_type="text/html; charset=UTF-8",
            charset="utf-8",
        )
    else:
        LOGGER.info(f"Web: {json.dumps(response, ensure_ascii=False, sort_keys=True)}")
        return render(
            request,
            "index.html",
            response | {"visits": get_number_visits(datetime.timedelta(days=1))},
        )


@ttl_cache()
def get_whois_result(ip_or_host: str) -> list[list[str]]:
    whois = sh.Command(WHOIS_FILE)
    try:
        whois_result = whois(ip_or_host)
    except (sh.ErrorReturnCode, sh.CommandNotFound):
        return [["未知", "未知"]]
    if not whois_result:
        return [["未知", "未知"]]
    return [line.split(": ", 2) for line in whois_result.splitlines()]


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


def get_ip_location_from_ip2region(ip_address: str) -> Dict:
    ip2region_result = IP2REGION_READER.searchByIPStr(ip_address).split("|")
    ip2region_result = [None if _ == "0" else _ for _ in ip2region_result]
    return {
        "ip": ip_address,
        "country": ip2region_result[0],
        "region": ip2region_result[1],
        "province": ip2region_result[2],
        "city": ip2region_result[3],
        "isp": ip2region_result[4],
        "database_name": "ip2region",
        "database_href": "https://gitee.com/lionsoul/ip2region/",
    }


def get_ip_location_from_geolite2(ip_address: str) -> Dict:
    try:
        geolite2_result = GEOLITE2_READER.city(ip_address)
        geolite2_location = {
            "ip": ip_address,
            "country": geolite2_result.country.names.get(
                "zh-CN", geolite2_result.country.name
            ),
            "region": None,
            "province": geolite2_result.subdivisions.most_specific.names.get(
                "zh-CN", geolite2_result.subdivisions.most_specific.name
            ),
            "city": geolite2_result.city.names.get("zh-CN", geolite2_result.city.name),
            "isp": None,
            "database_name": "GeoLite2",
            "database_href": "https://www.maxmind.com/",
        }
    except AddressNotFoundError:
        geolite2_location = {
            "ip": ip_address,
            "country": None,
            "region": None,
            "province": None,
            "city": None,
            "isp": None,
            "database_name": "GeoLite2",
            "database_href": "https://www.maxmind.com/",
        }
    return geolite2_location


@lru_cache(maxsize=1024)  # the ip location query is stable, thus do not need TTL
def get_ip_location(ip_address: str, database: str = "both") -> Dict:
    """query the ip location

    Args:
        ip_address: the ip address to query
        database: "both", "ip2region", "GeoLite2"

    None when the field is unknown
    """
    if database == "ip2region":
        return get_ip_location_from_ip2region(ip_address)
    elif database == "GeoLite2":
        return get_ip_location_from_geolite2(ip_address)
    else:  # database == "both"
        # use ip2region database to get the country name
        ip2region_location = get_ip_location_from_ip2region(ip_address)
        # try GeoLite2 database for ip address that is not in China
        if ip2region_location["country"] != "中国":
            geolite2_location = get_ip_location_from_geolite2(ip_address)
            if geolite2_location["country"]:
                return geolite2_location
        # fall back to ip2region database
        return ip2region_location


@ttl_cache()
def get_address(latitude: str | None, longitude: str | None) -> str | None:
    """get address from geo location by GEOLOCATOR

    return None if error happens or no address found
    """
    try:
        location = GEOLOCATOR.reverse(f"{latitude}, {longitude}", language="zh-cn")  # type: ignore
    except (ValueError, GeocoderUnavailable):
        return None
    if not location:
        return None
    return location.address  # type: ignore


@require_http_methods(["GET"])
def get_address_from_coordinates(request: WSGIRequest) -> JsonResponse:
    """get address from coordinates

    Returns:
        str: {"address": location.address}
    """
    latitude = request.GET.get("latitude")
    longitude = request.GET.get("longitude")
    address = get_address(latitude, longitude)
    return JsonResponse(
        {"address": address},
        json_dumps_params={"ensure_ascii": False, "indent": 2},
    )  # type: ignore


@require_http_methods(["GET"])
def get_headers(request: WSGIRequest) -> HttpResponse:
    headers = {}
    for attribute in sorted(dict(request.headers.items())):
        headers[attribute] = request.headers[attribute]
    return render(
        request,
        "headers.html",
        context={"headers": headers},
    )


@require_http_methods(["GET"])
def get_navigator(request: WSGIRequest) -> HttpResponse:
    return render(
        request,
        "navigator.html",
    )


def get_host_ip_from_url(url: str) -> tuple[Optional[str], Optional[str]]:
    """get ipv4 from url(or ip address string)

    Return
      (host, ip)
    """
    if not url:
        return None, None
    # try ipv4 address
    elif is_valid_ipv4(url):
        return None, url
    # try valid url
    elif host := urlparse(url).netloc:
        try:
            ip = socket.gethostbyname(host)
        except (socket.gaierror, UnicodeError):
            pass
        else:
            return host, ip
    # try host name
    else:
        try:
            ip = socket.gethostbyname(url)
        except (socket.gaierror, UnicodeError):
            pass
        else:
            return url, ip
    LOGGER.error(f"can not get ip from {url}")
    return None, None


@require_http_methods(["GET"])
def get_query(request: WSGIRequest) -> HttpResponse:
    host, ip_address = get_host_ip_from_url(request.GET.get("url", ""))
    context: Dict = {
        "ip": ip_address,
        "host": host,
        "country": "未知",
        "region": "未知",
        "province": "未知",
        "city": "未知",
        "isp": "未知",
        "database_name": "未知",
        "database_href": "未知",
        "whois_ip": [["未知", "未知"]],
        "whois_host": [["未知", "未知"]],
    }
    if ip_address:
        ip_location = get_ip_location(ip_address)
        whois_ip = {"whois_ip": get_whois_result(ip_address)}
        context |= ip_location | whois_ip
    # easy to get blocked if we check for host
    # if host:
    #     whois_host = {"whois_host": get_whois_result(host)}
    #     context |= whois_host
    return render(request, "query.html", context=context)


@require_http_methods(["GET"])
def get_whois(request: WSGIRequest) -> HttpResponse:
    ip_address = get_ip_address(request)
    return render(
        request,
        "whois.html",
        context={"whois": get_whois_result(ip_address)},
    )


@require_http_methods(["GET"])
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
    path("query", get_query),
    path("ips", get_ips),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
    path(
        "ads.txt",
        TemplateView.as_view(template_name="ads.txt", content_type="text/plain"),
    ),
]
application = get_wsgi_application()
application = WhiteNoise(
    application, root=os.path.join(BASE_DIR, "static/"), prefix="static/"
)

if __name__ == "__main__":
    execute_from_command_line(sys.argv)
