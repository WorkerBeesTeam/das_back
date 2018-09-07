from django.core.management.base import BaseCommand
from telegrambot.models import Bot

from applications.house_list.models import House

class Command(BaseCommand):
    help = 'Send critical message to telegram'

    def add_arguments(self, parser):        
        parser.add_argument('id', help='ID теплицы')
        parser.add_argument('text', help='Текст сообщения')
            
    def handle(self, *args, **options):
        house = House.objects.get(pk=int(options['id']))
        
        tg_group = house.team.telegramsubscriber_set.first()
        if tg_group:
            bot = Bot.objects.first()
            bot.send_message(tg_group.chat_id, options['text'])
#         bot.send_message(-238807498, options['text'])
