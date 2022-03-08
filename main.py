import sys, logging, os
from typing import Dict
from django.http import HttpResponse, JsonResponse
from django.urls import path
from django.conf import settings
from django.core.wsgi import get_wsgi_application
from django.core.management import execute_from_command_line
from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import render
from whitenoise import WhiteNoise
from ip2region.ip2Region import Ip2Region
from ipaddress import IPv4Address, AddressValueError
import geoip2.database

BASE_DIR = os.path.dirname(__file__)
DEBUG = os.environ.get("DEBUG", False) == "True"
SECRET_KEY = os.environ.get("SECRET_KEY", os.urandom(32))
logger = logging.getLogger(__name__)

# https://github.com/lionsoul2014/ip2region
ip2region_reader = Ip2Region("./ip2region/ip2region.db")
# https://geoip2.readthedocs.io/en/latest/
geolite2_reader = geoip2.database.Reader("./GeoLite2/GeoLite2-City.mmdb")


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


def get_index(request: WSGIRequest) -> HttpResponse:
    local_ip = get_ip_address(request)
    if not (query_ip := request.GET.get("ip")):
        query_ip = local_ip
    ip_location = get_ip_location(query_ip)
    if request.content_type == "application/json":
        return JsonResponse(ip_location)
    else:
        ip_location["local_ip"] = local_ip
        return render(request, "index.html", ip_location)


def get_ip_address(request: WSGIRequest) -> str:
    """to get the client ip address even if behind nginx

    ref:  https://stackoverflow.com/a/5976065
    """
    if x_forwarded_for := request.META.get("HTTP_X_FORWARDED_FOR"):
        ip_address = x_forwarded_for.split(",")[-1].strip()
    else:
        ip_address = request.META.get("REMOTE_ADDR")
    return ip_address


def get_ip_location(ip_address: str) -> Dict:
    """query the ip location"""
    INVALID_IP = "IP 地址错误"
    UNKNOWN_LOCATION = "未知"
    try:
        IPv4Address(ip_address)
    except AddressValueError:
        return {
            "ip": ip_address,
            "country": INVALID_IP,
            "region": INVALID_IP,
            "province": INVALID_IP,
            "city": INVALID_IP,
            "isp": INVALID_IP,
        }
    # use ip2region database to get the country name
    ip2region_result = (
        ip2region_reader.btreeSearch(ip_address)["region"].decode().split("|")
    )
    ip2region_result = [UNKNOWN_LOCATION if _ == "0" else _ for _ in ip2region_result]
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
                "region": UNKNOWN_LOCATION,
                "province": geolite2_result.subdivisions.most_specific.names.get(
                    "zh-CN", geolite2_result.subdivisions.most_specific.name
                ),
                "city": geolite2_result.city.names.get(
                    "zh-CN", geolite2_result.city.name
                ),
                "isp": UNKNOWN_LOCATION,
                "database_name": "GeoLite2",
                "database_href": "https://www.maxmind.com/",
            }
            return geolite2_location
        except geoip2.errors.AddressNotFoundError:
            pass
    # otherwise, fall back to use ip2region database
    return ip2region_location


urlpatterns = [path("", get_index)]
application = get_wsgi_application()
application = WhiteNoise(application, root="./static", prefix="static/")

if __name__ == "__main__":
    execute_from_command_line(sys.argv)
