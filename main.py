import sys, requests, logging, os
from typing import Dict
from django.http import HttpResponse, JsonResponse
from django.urls import path
from django.conf import settings
from django.core.wsgi import get_wsgi_application
from django.core.management import execute_from_command_line
from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import render
from whitenoise import WhiteNoise

BASE_DIR = os.path.dirname(__file__)
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
    ip_address = request.META.get("REMOTE_ADDR", None)
    ip_location = get_ip_location(ip_address)
    return render(request, "index.html", ip_location)


def get_json(request: WSGIRequest) -> JsonResponse:
    ip = request.META.get("REMOTE_ADDR", None)
    return JsonResponse(get_ip_location(ip))


def get_ip_location(ip: str) -> Dict:
    # API reference:
    #   https://market.aliyun.com/products/57002002/cmapi00046276.html#sku=yuncode4027600002
    # Calling this function should always return a dict with the following format
    ip_location = {"ip": ip, "province": None, "city": None, "isp": None}
    try:
        r = requests.get(
            url="http://cz88.rtbasia.com/search",
            params={"ip": ip},
            timeout=5,
            headers={
                "Authorization": "APPCODE b4e8f9eda03140c685525fd029ada70a",
            },
        ).json()
    except (
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        requests.exceptions.TooManyRedirects,
        requests.exceptions.JSONDecodeError,
    ):
        logger.exception("get_ip_location failed")
        return ip_location

    data = r.get("data", {"province": None, "city": None, "isp": None})
    ip_location["province"] = data.get("province", None)
    ip_location["city"] = data.get("city", None)
    ip_location["isp"] = data.get("isp", None)
    return ip_location


urlpatterns = [path("", get_index), path("json/", get_json)]
application = get_wsgi_application()
application = WhiteNoise(application, root="./static", prefix="static/")

if __name__ == "__main__":
    execute_from_command_line(sys.argv)
