"""
ASGI config for diplom project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from storage.consumers import *
from django.urls import path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diplom.settings')

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    'websocket': AuthMiddlewareStack( 
                                     URLRouter([
        path('ws/lenta/', LentaConsumer.as_asgi()),
        path('ws/disk/', DiskConsumer.as_asgi()),
    ])
    ),
})

