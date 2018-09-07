from telegrambot.bot_views.generic import TemplateCommandView, ListCommandView, DetailCommandView, \
    ListDetailCommandView
    
from telegrambot.models.auth import AuthToken
from applications.house_list.models import House as Author, TelegramSubscriber

class HelpView(TemplateCommandView):
    template_text = "bot/messages/help.txt"
    template_keyboard = "bot/messages/help_keyboard.txt"

class SubscribeView(TemplateCommandView):
    template_text = "bot/messages/subscribe.txt"
    def get_context(self, bot, update, **kwargs):
        already_subscribe = TelegramSubscriber.objects.filter(chat_id=update.message.chat_id)
        if already_subscribe:
            return { 'already_subscribe': True }
        
        token = AuthToken.objects.get(chat_api_id=update.message.chat_id)
        
        subscribe = TelegramSubscriber()
        subscribe.chat_id = update.message.chat_id
        subscribe.group = token.user.groups.first()
        subscribe.save()
        
        return None
    
class UnsubscribeView(TemplateCommandView):
    template_text = "bot/messages/unsubscribe.txt"
    def get_context(self, bot, update, **kwargs):
        subscribe = TelegramSubscriber.objects.filter(chat_id=update.message.chat_id)
        if subscribe:
            subscribe.delete()
            return None
        return { 'not_subscribe': True }
    
    
    
    
    

class StartView(TemplateCommandView):
    template_text = "bot/messages/command_start_text.txt"
    def get_context(self, bot, update, **kwargs):
        return kwargs
    
class UnknownView(TemplateCommandView):
    template_text = "bot/messages/command_unknown_text.txt"
    def get_context(self, bot, update, **kwargs):
        return { 'bot': bot, 'chat_id': update.message.chat_id }
    
class AuthorListView(ListCommandView):
    template_text = "bot/messages/command_author_list_text.txt"
    template_keyboard = "bot/messages/command_author_list_keyboard.txt"
    model = Author
    context_object_name = "authors"
    
class AuthorInverseListView(AuthorListView):
    ordering = "-name"

class AuthorDetailView(DetailCommandView):
    template_text = "bot/messages/command_author_detail_text.txt"
    context_object_name = "author"
    model = Author
    slug_field = 'name'
    
class AuthorListQueryView(AuthorListView):
    queryset = Author.objects.all

class AuthorDetailQueryView(AuthorDetailView):
    queryset = Author.objects
    
class AuthorCommandView(ListDetailCommandView):
    list_view_class = AuthorListView
    detail_view_class = AuthorDetailView

class AuthorCommandQueryView(ListDetailCommandView):
    list_view_class = AuthorListQueryView
    detail_view_class = AuthorDetailQueryView
    
class MessageView(TemplateCommandView):
    template_text = "bot/messages/unknown_message_text.txt"
    
class AuthorName(DetailCommandView):
    template_text = "bot/messages/regex_author_name_text.txt"
    context_object_name = "author"
    model = Author
    slug_field = 'name'
    
    def get_slug(self, **kwargs):
        return kwargs.get('name', None)
