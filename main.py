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

BASE_DIR = os.path.dirname(__file__)

# https://github.com/lionsoul2014/ip2region
searcher = Ip2Region("./ip2region/ip2region.db")

settings.configure(
    DEBUG=True,
    SECRET_KEY=r"uZ4HrjtDcBRiuEj9x#DPKXS&Z^F3rH%aJR82J*Au7^fnqvWbqd@5yzaz9ccu#N7T",
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

logger = logging.getLogger(__name__)


def get_index(request: WSGIRequest) -> HttpResponse:
    # /?ip=<ipv4 address>
    # return client IP without query
    if not (ip_address := request.GET.get("ip")):
        ip_address = get_ip_address(request)
    ip_location = get_ip_location(ip_address)
    if request.content_type == "application/json":
        return JsonResponse(ip_location)
    else:
        return render(request, "index.html", ip_location)


def get_ip_address(request: WSGIRequest) -> str:
    # to get the ip address even if behind nginx
    # ref:  https://stackoverflow.com/a/5976065
    if x_forwarded_for := request.META.get("HTTP_X_FORWARDED_FOR"):
        ip_address = x_forwarded_for.split(",")[-1].strip()
    else:
        ip_address = request.META.get("REMOTE_ADDR")
    return ip_address


def get_ip_location(ip_address: str) -> Dict:
    INVALID_IP_ADDRESS = "IP 地址错误"
    UNKNOWN_LOCATION_FIELD = "未知"
    try:
        IPv4Address(ip_address)
        ip2region_result = (
            searcher.btreeSearch(ip_address)["region"].decode().split("|")
        )
        ip2region_result = [
            UNKNOWN_LOCATION_FIELD if _ == "0" else _ for _ in ip2region_result
        ]
        ip_location = {
            "ip": ip_address,
            "country": ip2region_result[0],
            "region": ip2region_result[1],
            "province": ip2region_result[2],
            "city": ip2region_result[3],
            "isp": ip2region_result[4],
        }
    except AddressValueError:
        ip_location = {
            "ip": ip_address,
            "country": INVALID_IP_ADDRESS,
            "region": INVALID_IP_ADDRESS,
            "province": INVALID_IP_ADDRESS,
            "city": INVALID_IP_ADDRESS,
            "isp": INVALID_IP_ADDRESS,
        }
    return ip_location


urlpatterns = [path("", get_index)]
application = get_wsgi_application()
application = WhiteNoise(application, root="./static", prefix="static/")

if __name__ == "__main__":
    execute_from_command_line(sys.argv)
