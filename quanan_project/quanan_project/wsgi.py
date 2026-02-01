# WSGI config for quanan_project project
# https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quanan_project.settings')

application = get_wsgi_application()
