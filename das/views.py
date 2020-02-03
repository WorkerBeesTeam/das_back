# import subprocess
# import re
# import os
# import json

# from django.contrib import admin
# from django.contrib.auth.models import User
# from django.urls import path, re_path
# from django.conf.urls import include, url
# from django.conf import settings
# from django.shortcuts import render_to_response, render
# from django.views.generic import TemplateView
# from wsgiref.util import FileWrapper
# 
# 
# from applications import add_db_to_connections
# from .tool import checkConnection
# from applications.scheme.export import init_excel, export_log2excel
# Create your views here.

# from applications import get_current_language
# from applications.scheme_list import views, models as list_models

# ---
# from django.views.decorators.http import require_http_methods

from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.static import serve

from django.utils.translation import get_language_from_request

def get_current_language(request): 
    current_lang = request.GET.get('lang', None)
    if current_lang == None:
        current_lang = get_language_from_request(request)
    if current_lang in ['ru', 'en', 'fr', 'es']:
        return current_lang
    return 'ru'

@ensure_csrf_cookie
def show_main(req):
    return HttpResponseRedirect('/' + get_current_language(req) + '/')

@ensure_csrf_cookie
def show_any_path(req, lang, path, document_root):
    if not lang:
        lang = get_current_language(req)
        return HttpResponseRedirect('/' + lang + '/' + path)
    try:
        path = lang + '/' + path
        return serve(req, path, document_root + '/')
    except:
        return serve(req, '/' + lang + '/index.html', document_root)

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@ensure_csrf_cookie
def get_csrf(req):
    return HttpResponse(status=204)

