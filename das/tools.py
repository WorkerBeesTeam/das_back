from django.shortcuts import get_list_or_404

from . import models

def get_scheme(request):
    return get_list_or_404(models.Scheme, id=int(request.GET.get('scheme_id', 0)), groups__scheme_group_user__user_id=request.user.id)[0]
