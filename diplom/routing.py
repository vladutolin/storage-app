from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from storage.consumers import MyConsumer
import os

from django.core.asgi import get_asgi_application

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': URLRouter([
        path('ws/my_endpoint/', MyConsumer.as_asgi()),
    ]),
})