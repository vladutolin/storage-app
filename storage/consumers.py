import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diplom.settings')
django.setup()
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.template.loader import render_to_string
from .models import *
from .forms import *
from channels.db import database_sync_to_async
from django.middleware.csrf import get_token
from channels.middleware import BaseMiddleware

class CSRFTokenMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        scope['csrf_token'] = get_token(scope['session'])
        return await super().__call__(scope, receive, send)

class LentaConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add('lenta_group', self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('lenta_group', self.channel_name)

    async def receive(self, text_data):
        pass

    async def lenta_message(self, event):
        csrf_token = self.scope.get('csrf_token')
        # sub = Subscription.objects.filter(subscriber=self.scope.get('user')).values_list('subscriberTo', flat=True)
        # posts = Posts.objects.filter(author__in=sub)
        # comments = Comment.objects.filter(post__in=posts)
        # html = render_to_string('storage/post_template.html', {'posts': posts, 'comments': comments})
        html = await self.get_posts(csrf_token)
        await self.send(text_data=html)
    
    
    @database_sync_to_async
    def get_posts(self, csrf_token):
        print(self.scope.get('user'))
        sub = Subscription.objects.filter(subscriber=self.scope.get('user')).values_list('subscriberTo', flat=True)
        posts = Posts.objects.filter(author__in=sub)
        comments = Comment.objects.filter(post__in=posts)
        form_class = AddComment
        html = render_to_string('storage/post_template.html', {'posts': posts, 'comments': comments, 'form':form_class(),'csrf_token': csrf_token})
        return html

class DiskConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add('disk_group', self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('disk_group', self.channel_name)

    async def receive(self, text_data):
        pass

    async def disk_message(self, event):
        html = await self.get_items()
        await self.send(text_data=html)
    
    
    @database_sync_to_async
    def get_items(self):
        q = Folder.objects.filter(owner=self.scope.get('user'), parent=None)
        q1 = File.objects.filter(owner=self.scope.get('user'), folder=None)
    
       
        html = render_to_string('storage/disk_update.html', {'folder': q, 'files': q1 })
        return html