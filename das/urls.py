"""das URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings

from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token, verify_jwt_token

from .api.v1.routes import urlpatterns as api_urls
from .updates import urlpatterns as updates_urls
from .auth import tg_auth

from . import views
from .export import export_excel

auth_urls = [
    path('auth/', obtain_jwt_token),
    path('refresh/', refresh_jwt_token),
    path('verify/', verify_jwt_token),
]

urlpatterns = [
    path('admin/', admin.site.urls),

    # API:V1
    path('api/v1/', include(api_urls)),
    path('api/token/', include(auth_urls)),
    path('api/tg_auth/', tg_auth),

    path('updates/', include(updates_urls)),

    path('export/excel/', export_excel),

    path('', views.show_main, name='index'),
    path('get_csrf', views.get_csrf),

    re_path(r'^(?P<lang>(ru|en|fr|es|mn))$', views.show_any_path, {
        'path': 'index.html',
        'document_root': settings.MEDIA_ROOT,
    }),
    re_path(r'^(?P<lang>(ru|en|fr|es|mn))/(?P<path>(?!api).*)$', views.show_any_path, {
        'document_root': settings.MEDIA_ROOT,
    }),
    re_path(r'^(?P<path>(?!api).*)$', views.show_any_path, {
        'lang': None,
        'document_root': settings.MEDIA_ROOT,
    }),
]
