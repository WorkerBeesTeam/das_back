from django.db import connections

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

