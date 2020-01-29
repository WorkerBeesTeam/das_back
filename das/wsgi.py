"""
WSGI config for das project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

settings_module = 'das.settings.prod'
try:
    from mod_wsgi import process_group
    if process_group:
        settings_module = process_group
except ImportError:
    pass

print('Django settings module is {0}'.format(settings_module))
# os.environ['DJANGO_SETTINGS_MODULE'] = settings_module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)

application = get_wsgi_application()
