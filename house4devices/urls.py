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

from applications.api.v1.routes import api_router
from applications.house_list import views
import subprocess

@ensure_csrf_cookie
def show_main(req):
    return render_to_response('index.html')

@ensure_csrf_cookie
def showAnyPath(req, path, document_root):
    try:
        return serve(req, path, document_root)
    except:
        return serve(req, 'index.html', document_root)

def update_file(req):
    upd_file = open(settings.MEDIA_ROOT + '/update.tar.gz', 'rb')
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

def version_file(req):
    ver_file = open(settings.MEDIA_ROOT + '/version.json', 'rb')
    ver = ver_file.read()

    name = req.GET.get('name', '?')
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
    print("Check version: {0} from: {1} {2} current: {3}".format(req.GET.get('version', '?'), name, get_client_ip(req), cur_ver))

    return HttpResponse(ver, content_type='application/json')

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


def upload_firmware(req):
   # os.system("/opt/dai/DaiServer -l a")        
    if req.method == 'POST' and req.FILES['fileKey']:
        project_id = req.GET.get('id')
        devitem_id = req.GET.get('item_id')
        input_file = req.FILES['fileKey']
        file_name = input_file.name
        file_path = '/var/tmp/firmware'
        #if (house_id != None):
        #    file_path += '.' + house_id
        #if (item_id != None):
        #    file_path += '.' + item_id
        file_path += '.dat'
        with open(file_path, 'wb+') as destination:
            for chunk in input_file.chunks():
                destination.write(chunk)
        args = ['/usr/bin/sudo', '-u', 'dai', settings.DAI_SERVER_PATH, '-l', '--send_file', project_id, devitem_id, file_name, file_path]
        print(subprocess.call(args))
       # print('hello' + str(subprocess.call(['/opt/dai/DaiServer -l a'], shell=True)))
 
        return HttpResponse(status = 200)
    return HttpResponse(status = 204)


urlpatterns = [
    path('admin/', admin.site.urls),

    url(r'^telegrambot/', include(('telegrambot.urls', 'telegrambot'))),

    # API:V1
    url(r'^api/v1/', include(api_router.urls)),
    url(r'^api/token/auth/', obtain_jwt_token),
    url(r'^api/token/refresh/', refresh_jwt_token),
    url(r'^api/token/verify/', verify_jwt_token),

    url(r'^check_version', version_file),
    url(r'^update_file', update_file),

    url(r'^export/excel', views.export_excel),
    url(r'^upload_t', upload_t),
    url(r'^api/v1/upload/firmware/$', upload_firmware),

    url(r'^manage/(?P<houseId>\d+)$', lambda req, houseId: HttpResponseRedirect("/house/{0}/manage".format(houseId))),
    url(r'^$', show_main, name='index'),
    re_path(r'^(?P<path>(?!api).*)$', showAnyPath, {
        'document_root': settings.MEDIA_ROOT,
    }),
]
