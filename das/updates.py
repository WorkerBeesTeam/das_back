import re
import json
from django.urls import path
from django.conf import settings

from das import models

def check_update_accepted(name):
    if not settings.UPDATE_ACCEPTED_LIST:
        return True

    with open(settings.UPDATE_ACCEPTED_LIST, 'r') as f:
        for line in f:
            pattern = line[:-1]
            if pattern and re.match(pattern, name):
                return True
    return False

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def updates_check(req):
    ver_file = open(settings.MEDIA_ROOT + '/version.json', 'rb')
    ver = ver_file.read()

    name = req.GET.get('name', '?')
    client_ver = req.GET.get('version', '?')
    doc = None
    try:
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
        h = models.Scheme.objects.get(name=name)
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

def updates_file(req):
    name = req.GET.get('name', '?')
    if not check_update_accepted(name):
        return HttpResponse(status=400)

    version = req.GET.get('version', '0.0.0')
    if not re.match('^\d{1,4}\.\d{1,4}\.\d{1,4}$', version):
        version = '0.0.0'

    file_name = settings.MEDIA_ROOT + '/updates/update.' + version + '.tar.gz'

    if not os.path.isfile(file_name):
        return HttpResponse(status=204)

    upd_file = open(file_name, 'rb')
    response = HttpResponse(FileWrapper(upd_file), content_type='application/tar+gzip')
    response['Content-Disposition'] = 'attachment; filename="update.tar.gz"'
    return response

# from django.views.decorators.csrf import csrf_exempt
# import random
# import os
# @csrf_exempt
# def upload_t(req):
#     if req.method == 'POST':
#         email = req.GET['email']
#         f = req.FILES['f']
#         file_name = '/var/tmp/upload_t_' + str(random.randint(100, 999)) + '.txt.gz'
#         with open(file_name, 'wb+') as destination:
#             for chunk in f.chunks():
#                 destination.write(chunk)
#         os.system("/opt/send_t {0} {1}".format(file_name, email))        
#     return HttpResponse(status=204)

urlpatterns = [
    path('check/', updates_check),
    path('file/', updates_file),

#    path('upload_t/', upload_t),
]

