from django.core.management.base import BaseCommand
from django.core.management.utils import get_random_secret_key

import datetime
from das import models as m

class Command(BaseCommand):
    help = 'Fill outdated value log as today'

    def handle(self, *args, **options):
        now = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        now = int(now * 1000)
        day_ago = now - (24 * 3600000)
        
        scheme_list = m.Log_Value.objects.filter(timestamp_msecs__gte=day_ago).values_list('scheme_id', flat=True).distinct()
        
        scheme_full_list = list(scheme_list)
        scheme_full_list += m.Scheme.objects.filter(id__in=scheme_list, parent_id__isnull=False).values_list('parent_id', flat=True).distinct()
        
        items = m.Log_Value.objects.filter(timestamp_msecs__gte=day_ago, timestamp_msecs__lte=now).values_list('item_id', flat=True).distinct()
        items = m.Device_Item.objects.filter(scheme_id__in=scheme_full_list, type__save_algorithm__gt=1).exclude(id__in=items).values_list('id', flat=True)
        
        if not items:
            print('No outdated items found')
            return

        print('Find outdated items count:', len(items))

        for i in items:
            for s in scheme_list:
                v = m.Log_Value.objects.filter(scheme_id=s, timestamp_msecs__lt=day_ago, item_id=i)[:1]
                if not v:
                    v = m.Log_Value()
                    v.scheme_id = s
                    v.item_id = i

                    value = m.Device_Item_Value.objects.filter(scheme_id=s, item_id=i)
                    if value:
                        v.value = value[0].value
                else:
                    v = v[0]
                v.timestamp_msecs = now
                v.pk = None
                v.save()

                print('Added log for item', i, 'in scheme', s, 'with value', v.value)

