from telegrambot.handlers import command, unknown_command, regex, message 
from telegrambot.bot_views.decorators import login_required

from house4devices import commands_views as views

urlpatterns = [
    command('start', views.StartView.as_command_view()),
    
    command('help', views.HelpView.as_command_view()),
    
    command('subscribe', login_required(views.SubscribeView.as_command_view())),
    command('unsubscribe', login_required(views.UnsubscribeView.as_command_view())),
    
    command('author_inverse', views.AuthorInverseListView.as_command_view()),
    command('author_query', views.AuthorCommandQueryView.as_command_view()),
    regex(r'^author_(?P<name>\w+)', views.AuthorName.as_command_view()),
    command('author_auth', login_required(views.AuthorCommandView.as_command_view())),
    command('author', views.AuthorCommandView.as_command_view()), 
    unknown_command(views.UnknownView.as_command_view()),
    message(views.MessageView.as_command_view())
]
