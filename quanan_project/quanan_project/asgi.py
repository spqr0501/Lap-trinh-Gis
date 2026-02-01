# ASGI config for quanan_project project
# https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quanan_project.settings')

application = get_asgi_application()
