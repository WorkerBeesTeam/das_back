from django.core.management.base import BaseCommand
from django.db.utils import DEFAULT_DB_ALIAS
from django.utils import timezone

from applications.scheme.models import Logs, EventLog
class Command(BaseCommand):
    help = 'Clear old from logs and eventLog'
    
    def add_arguments(self, parser):
        parser.add_argument('--database', help='База данных', default=DEFAULT_DB_ALIAS)
        parser.add_argument('--days', help='Количество допустимых дней', default=31)
        
    def handle(self, *args, **options):
        max_date = timezone.make_aware(timezone.datetime.today() - timezone.timedelta(days=int(options['days'])))
        
        Logs.objects.using(options['database']).filter(date__lt=max_date).delete()
        EventLog.objects.using(options['database']).filter(date__lt=max_date).delete()

