from django.db import connections
from django.utils.translation import get_language_from_request

def gen_db_name(prefix, database_id):
    return '{0}_{1}'.format(prefix, database_id)
def add_db_to_connections(database_id):
    if not database_id in connections.databases:
        newDatabase = connections.databases['default'].copy()
        newDatabase["id"] = database_id
        newDatabase['NAME'] = gen_db_name(newDatabase['NAME'], database_id)
        connections.databases[database_id] = newDatabase
        return newDatabase
    return connections.databases[database_id]

def get_current_language(request): 
    current_lang = request.GET.get('lang', None)
    if current_lang == None:
        current_lang = get_language_from_request(request)
    if current_lang in ['ru', 'en', 'fr', 'es']:
        return current_lang
    return 'ru'
