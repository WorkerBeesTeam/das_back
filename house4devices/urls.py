"""houses URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
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
from django.urls import path, re_path
from django.conf.urls import include, url
from django.conf import settings
from django.shortcuts import render_to_response
from django.views.generic import TemplateView
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.static import serve
from django.http import HttpResponse, HttpResponseRedirect
from wsgiref.util import FileWrapper

from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token, verify_jwt_token

from applications import get_current_language
from applications.api.v1.routes import urlpatterns as api_urlpatterns
from applications.house_list import views, models as list_models
import subprocess
import re
import os

@ensure_csrf_cookie
def show_main(req):
    return HttpResponseRedirect('/' + get_current_language(req) + '/')

@ensure_csrf_cookie
def showAnyPath(req, lang, path, document_root):
    if not lang:
        lang = get_current_language(req)
        return HttpResponseRedirect('/' + lang + '/' + path)
    try:
        path = lang + '/' + path
        return serve(req, path, document_root + '/')
    except:
        return serve(req, '/' + lang + '/index.html', document_root)

def update_file(req):
    name = req.GET.get('name', '?')
    version = req.GET.get('version', '')
    if not re.match('^\d{1,4}\.\d{1,4}\.\d{1,4}$', version):
        version = '0.0.0'

    file_name = settings.MEDIA_ROOT + '/updates/update.' + version + '.tar.gz'

    if not os.path.isfile(file_name):
        return HttpResponse(status=204)

    upd_file = open(file_name, 'rb')
    response = HttpResponse(FileWrapper(upd_file), content_type='application/tar+gzip')
    response['Content-Disposition'] = 'attachment; filename="update.tar.gz"'
    return response

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def check_update_accepted(name):
    with open('/opt/dai/web/update_accepted.list', 'r') as f:
        for line in f:
            pattern = line[:-1]
            if pattern and re.match(pattern, name):
                return True
    return False

def check_version(req):
    ver_file = open(settings.MEDIA_ROOT + '/version.json', 'rb')
    ver = ver_file.read()

    name = req.GET.get('name', '?')
    client_ver = req.GET.get('version', '?')
    doc = None
    try:
        import json
        doc = json.loads(ver.decode('utf-8'))
        cur_ver = doc.get('version', '?')
    except Exception as e:
        print(e)
        cur_ver = '?'
    except:
        print('error')
        cur_ver = '?'
    print("Check version: {0} from: {1} {2} current: {3}".format(client_ver, name, get_client_ip(req), cur_ver))

    try:
        h = list_models.House.objects.get(name=name)
        h.version = client_ver
        h.save()
    except:
        pass

    if not check_update_accepted(name):
        doc['version'] = client_ver
    elif not client_ver or client_ver == '?':
        doc['version'] = '0.0.0'
    else:
        next_version = get_next_version(client_ver)
        if (version_compare(next_version, cur_ver) > 0):
            doc['version'] = client_ver
        else:
            doc['version'] = next_version

    return HttpResponse(json.dumps(doc), content_type='application/json')


def get_next_version(curr_version):
    file_list = os.listdir(settings.MEDIA_ROOT + '/updates/')
    expr = re.compile('^update\.(\d{1,4})\.(\d{1,4})\.(\d{1,4})\.tar\.gz$')
    version_list = []
    for file_name in file_list:
        v = expr.match(file_name)
        if v:
            version_list.append((v.group(1), v.group(2), v.group(3)))

    tmp = curr_version.split(".")
    version_int = (tmp[0], tmp[1], tmp[2])
    version_list.append(version_int)
    version_list.sort()

    ver_position = 0
    for position, item in enumerate(version_list):
        if item == version_int:
            ver_position = position
    if ver_position >= (len(version_list) - 1):
        return curr_version
    else:
        return '.'.join(str(x) for x in version_list[ver_position + 1])


def version_compare(ver1, ver2): 
    
    arr1 = ver1.split(".")
    arr2 = ver2.split(".")

    i = 0 
    while(i < len(arr1)): 
        if int(arr2[i]) > int(arr1[i]): 
            return -1
        if int(arr1[i]) > int(arr2[i]): 
            return 1
        i += 1
          
    return 0

from django.views.decorators.csrf import csrf_exempt
import random
import os
@csrf_exempt
def upload_t(req):
    if req.method == 'POST':
        email = req.GET['email']
        f = req.FILES['f']
        file_name = '/var/tmp/upload_t_' + str(random.randint(100, 999)) + '.txt.gz'
        with open(file_name, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)
        os.system("/opt/send_t {0} {1}".format(file_name, email))        
    return HttpResponse(status=204)

@ensure_csrf_cookie
def get_csrf(req):
    return HttpResponse(status=204)

urlpatterns = [
    path('admin/', admin.site.urls),

    # API:V1
    url(r'^api/v1/', include(api_urlpatterns)),
    url(r'^api/token/auth/', obtain_jwt_token),
    url(r'^api/token/refresh/', refresh_jwt_token),
    url(r'^api/token/verify/', verify_jwt_token),

    url(r'^check_version', check_version),
    url(r'^update_file', update_file),

    url(r'^export/excel_pouring', views.export_excel_pouring),
    url(r'^export/excel_idle', views.export_excel_idle),
    url(r'^export/excel', views.export_excel),
    url(r'^upload_t', upload_t),

    url(r'^manage/(?P<houseId>\d+)$', lambda req, houseId: HttpResponseRedirect("/house/{0}/manage".format(houseId))),
    url(r'^$', show_main, name='index'),
    url(r'^get_csrf$', get_csrf),
    re_path(r'^(?P<lang>(ru|en|fr|es|mn))$', showAnyPath, {
        'path': 'index.html',
        'document_root': settings.MEDIA_ROOT,
    }),
    re_path(r'^(?P<lang>(ru|en|fr|es|mn))/(?P<path>(?!api).*)$', showAnyPath, {
        'document_root': settings.MEDIA_ROOT,
    }),
    re_path(r'^(?P<path>(?!api).*)$', showAnyPath, {
        'lang': None,
        'document_root': settings.MEDIA_ROOT,
    }),
]
