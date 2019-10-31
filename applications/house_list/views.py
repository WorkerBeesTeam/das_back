from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST, require_http_methods

from rest_framework_jwt.serializers import VerifyJSONWebTokenSerializer #, ValidationError

from applications import add_db_to_connections
from .tool import checkConnection
from applications.house.export import init_excel, export_log2excel
from applications.house.export_idle import export_idle
from applications.house.export_pouring import export_pouring2excel
# Create your views here.

@require_POST
def export_excel(req):
    auth = req.META.get('HTTP_AUTHORIZATION')
    valid_data = VerifyJSONWebTokenSerializer().validate({'token': auth[4:]})
    req.user = valid_data['user']

    def get_conn_name(proj):
        add_db_to_connections(proj.name)
        return proj.name
    # house, conn_name = checkConnection(req)

    return export_log2excel(req, get_conn_name)


@require_http_methods(["GET", "POST"])
def export_excel_idle(req):
    # TODO: code duplication
    auth = req.META.get('HTTP_AUTHORIZATION')
    valid_data = VerifyJSONWebTokenSerializer().validate({'token': auth[4:]})
    req.user = valid_data['user']

    def get_conn_name(proj):
        add_db_to_connections(proj.name)
        return proj.name

    return export_idle(req, get_conn_name)


@require_http_methods(["GET", "POST"])
def export_excel_pouring(req):
    # TODO: code duplication
    auth = req.META.get('HTTP_AUTHORIZATION')
    valid_data = VerifyJSONWebTokenSerializer().validate({'token': auth[4:]})
    req.user = valid_data['user']

    def get_conn_name(proj):
        add_db_to_connections(proj.name)
        return proj.name

    return export_pouring2excel(req, get_conn_name)

