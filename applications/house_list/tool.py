from django.shortcuts import get_object_or_404

from applications import add_db_to_connections
from . import models

def checkConnection(request):
    house = get_object_or_404(models.House, id=int(request.GET.get('id', 0)), teams__pk=request.user.employee.team_id)
    add_db_to_connections(house.name)
    return house, house.name
