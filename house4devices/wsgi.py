"""
WSGI config for houses project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

try:
    from mod_wsgi import process_group
except ImportError:
    settings_module = 'house4devices.settings.prod'
else:
    settings_module = process_group

if not settings_module:
    settings_module = "house4devices.settings.prod"

print('Django settings module is {0}'.format(settings_module))

os.environ['DJANGO_SETTINGS_MODULE'] = settings_module
#os.environ.setdefault("DJANGO_SETTINGS_MODULE", "house4devices.settings.prod")

application = get_wsgi_application()
