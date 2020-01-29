from django.shortcuts import get_object_or_404

from applications import add_db_to_connections
from . import models

def checkConnection(request, team_id=None):
    if not team_id:
        team_id = request.user.employee.team_id
    house = get_object_or_404(models.House, id=int(request.GET.get('id', 0)), teams__pk=team_id)
    add_db_to_connections(house.name)
    return house, house.name
