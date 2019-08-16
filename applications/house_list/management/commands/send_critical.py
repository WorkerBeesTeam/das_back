from django.core.management.base import BaseCommand
from telegrambot.models import Bot
import telegram

from applications.house_list.models import House

class Command(BaseCommand):
    help = 'Send critical message to telegram'

    def add_arguments(self, parser):        
        parser.add_argument('id', help='ID теплицы')
        parser.add_argument('text', help='Текст сообщения')
            
    def handle(self, *args, **options):
        text = options['text']
        if text:
            house = House.objects.get(pk=int(options['id']))
            text = '*' + house.title + "*\n" + text
            teams = house.teams.all()
            bot = Bot.objects.first()
            for team in teams:
#                if team.id == 21:
                tg_groups = team.telegramsubscriber_set.all()
                for tg_group in tg_groups:
                    bot.send_message(tg_group.chat_id, text, parse_mode=telegram.ParseMode.MARKDOWN)
