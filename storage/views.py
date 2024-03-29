from typing import Any, Dict, Optional
from django import http
from django.db import models
from django.db.models.query import QuerySet
from django.http.response import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseNotFound, Http404
from django.views.generic import ListView, DetailView, CreateView, TemplateView, DeleteView, UpdateView, View
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.http import FileResponse, HttpResponseForbidden
from django.conf import settings
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

channel_layer = get_channel_layer()

from .models import *
from .forms import *


# Create your views here.


class Home(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('disk')
        context = {
            'title': 'Storage'
        }
        return render(request, 'storage/index.html', context)


class RegisterUser(CreateView):
    form_class = RegisterUserForm
    template_name = 'storage/register.html'
    success_url = reverse_lazy('login')
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('disk')
        return super().get(request)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Регистарция'
        return context
    

class LoginUser(LoginView):
    form_class = LoginUserForm
    template_name = 'storage/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('disk')
        return super().get(request)
            
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Авторизация'
        return context
    
    def get_success_url(self):
        return reverse_lazy('disk')
    

def logout_user(request):
    logout(request)
    return redirect('login')
    

class AddFile(LoginRequiredMixin, CreateView):
    form_class = AddFolderForm
    template_name = 'storage/addfile.html'
    success_url = reverse_lazy('disk')
    login_url = reverse_lazy('disk')
    raise_exception = True
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class Disk(LoginRequiredMixin, CreateView, ListView):
    model = File
    template_name = 'storage/disk.html'
    context_object_name = 'disk'
    form_class = AddFileForm
    form_class_folder = AddFolderForm
    success_url = reverse_lazy('disk')
    raise_exception = True
    
    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['upload'] = self.form_class()
        context['new_folder'] = self.form_class_folder()
        context['selected'] = 1
        context['title'] = 'Диск'
        return context
    
    def post(self, request, *args, **kwargs):
        form_file = self.form_class(request.POST, request.FILES)
        form_folder = self.form_class_folder(request.POST)
        if form_file.is_valid():
            form_file.instance.owner = self.request.user
            form_file.save()

        if form_folder.is_valid():
            folder = form_folder.save(commit=False)
            folder.owner = self.request.user
            folder.save()
        channel_layer = get_channel_layer()
        async def send_disk_message():
            await channel_layer.group_send(
                'disk_group',
                {'type': 'disk_message', 'content': 'Новое сообщение в ленте'}
            )
        async_to_sync(send_disk_message)()
        return redirect('disk')
    
    def get_queryset(self):
        q = list(Folder.objects.filter(owner=self.request.user, parent=None))
        q1 = list(File.objects.filter(owner=self.request.user, folder=None))
        return q + q1
    
    def get_success_url(self):
        return reverse_lazy('disk')

class DiskFolder(LoginRequiredMixin, CreateView, ListView):
    model = Folder
    template_name = 'storage/diskF.html'
    context_object_name = 'disk'
    form_class = AddFileForm
    form_class_folder = AddFolderForm
    
    raise_exception = True
    
    def get(self, request, folder_path):
        
        try:
            folder = Folder.objects.filter(path=folder_path, owner=request.user)[0]
        except Folder.DoesNotExist:
            return HttpResponseForbidden("У вас нет доступа к этой папке.")
        
        if folder.owner != request.user:
            return HttpResponseForbidden("У вас нет доступа к этой папке.")
        return super().get(request, folder_path)
    
    def post(self, request, *args, **kwargs):
        form_file = self.form_class(request.POST, request.FILES)
        form_folder = self.form_class_folder(request.POST)

        if form_file.is_valid():
            form_file.instance.owner = self.request.user
            form_file.instance.folder = Folder.objects.filter(path=self.kwargs['folder_path'], owner=self.request.user)[0]
            form_file.save()

        if form_folder.is_valid():
            folder = form_folder.save(commit=False)
            folder.owner = self.request.user
            folder.parent = Folder.objects.filter(path=self.kwargs['folder_path'], owner=self.request.user)[0]
            folder.save()

        return redirect(reverse('folder', kwargs={'folder_path': self.kwargs['folder_path']},))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['upload'] = self.form_class()
        context['new_folder'] = self.form_class_folder()
        context['selected'] = 1
        context['title'] = 'Диск'
        return context
    
    
    def get_queryset(self):
        q = list(Folder.objects.filter(owner=self.request.user, parent__path=self.kwargs['folder_path']))
        q1 = list(File.objects.filter(owner=self.request.user, folder__path=self.kwargs['folder_path']))
        return q + q1

    
    
@login_required
def show_file(request, file_id):
    obj = File.objects.get(id=file_id)
    if request.user == obj.owner:
        filename = obj.file.path
        response = FileResponse(open(filename, 'rb'))
        return response
    return HttpResponse('<h1>Нет доступа к файлу<h1>')

class DeleteFile(LoginRequiredMixin, DeleteView):
    model = File
    template_name = 'storage/delete_file.html'
    success_url = reverse_lazy('disk')
    
    def form_valid(self, request, *args, **kwargs):
        file_object = self.get_object()
        b = os.path.join(settings.BASE_DIR, 'media')
        file_path =os.path.join(b, str(file_object.file))
        if os.path.exists(file_path):
            os.remove(file_path)
        file_object.delete()
        
        channel_layer = get_channel_layer()
        async def send_disk_message():
            await channel_layer.group_send(
                'disk_group',
                {'type': 'disk_message', 'content': 'Удален файл'}
            )
    
        async_to_sync(send_disk_message)()

        return redirect('disk')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Удаление файла'
        return context
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(owner=self.request.user)
    
class DeleteFolder(LoginRequiredMixin, DeleteView):
    model = Folder
    template_name = 'storage/delete_folder.html'
    success_url = reverse_lazy('disk')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Удаление папки'
        return context
    
    def form_valid(self, request, *args, **kwargs):
        folder = self.get_object()
        file = File.objects.filter(folder=folder)
        b = os.path.join(settings.BASE_DIR, 'media')
        for i in file:
            file_path =os.path.join(b, str(i.file))
            print(file_path)
            if os.path.exists(file_path):
                os.remove(file_path)
            
        folder.delete()

        return redirect('disk')
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(owner=self.request.user)
    
    
class Profile(LoginRequiredMixin, CreateView, ListView):
    model = User
    template_name = 'storage/profile.html'
    success_url = 'profile'
    context_object_name = 'posts'
    form_class = AddPostsForm
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subs = Subscription.objects.filter(subscriberTo=self.request.user).count()
        context['subs'] = subs
        context['selected'] = 3
        context['title'] = 'Профиль'
        return context
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def post(self, request):
        
        form = self.form_class(request.POST, user=self.request.user)
        if form.is_valid():
            form.instance.author = self.request.user
            form.save()
        channel_layer = get_channel_layer()
        async def send_lenta_message():
            await channel_layer.group_send(
                'lenta_group',
                {'type': 'lenta_message', 'content': 'Новое сообщение в ленте'}
            )
    
        async_to_sync(send_lenta_message)()
        return redirect('profile')
    
    def get_queryset(self):
         return Posts.objects.filter(author=self.request.user)
     


class EditProfile(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'storage/editprofile.html'
    success_url = 'profile'
    form_class = EditProfileForm
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Редактирование профиля'
        return context

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy('profile')


class UserProfile(LoginRequiredMixin, CreateView, DetailView):
    model = User
    template_name = 'storage/user_profile.html'
    form_class = AddComment
    context_object_name = 'user_info'
    def get_object(self, queryset=None):
        username = self.kwargs['username']
        return User.objects.get(username=username)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        posts = Posts.objects.filter(author=user)
        comments = Comment.objects.filter(post__in=posts)
        context['posts'] = posts
        context['comments'] = comments
        if Subscription.objects.filter(subscriber=self.request.user, subscriberTo=user).exists():
            context['subs'] = 0
        else:
            context['subs'] = 1
        context['title'] = user.username
        return context
    
    def post(self, request):
        form = self.form_class(request.POST)
        
        
        if form.is_valid():
            form.instance.author = self.request.user
            form.save()
        
        return redirect('user_profile', username=self.kwargs['username'])

@login_required
def plus_sub(request, username):
    if request.method == 'POST':
        button_value = request.POST.get('sub')
        if button_value == 'submit':
            userTo = User.objects.get(username=username)
            new_sub = Subscription(subscriber=request.user, subscriberTo=userTo)
            new_sub.save()
    
    return redirect('user_profile', username=username)


@login_required
def minus_sub(request, username):
    userTo = User.objects.get(username=username)
    sub = Subscription.objects.filter(subscriber=request.user, subscriberTo=userTo)
    
    if request.method == 'POST':
        sub.delete()
        
    return redirect('user_profile', username=username)
    
    
    
@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Posts, pk=post_id)
    
    if request.method == 'POST':
        form = AddComment(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
    previous_page = request.META.get('HTTP_REFERER')
    return redirect(previous_page)
    


class Lenta(LoginRequiredMixin, CreateView, ListView):
    model = Posts
    template_name = 'storage/lenta.html'
    form_class = AddComment
    context_object_name = 'lenta'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subs = Subscription.objects.filter(subscriber=self.request.user).count()
        context['title'] = 'Лента'
        context['subs'] = subs
        sub = Subscription.objects.filter(subscriber=self.request.user).values_list('subscriberTo', flat=True)
        posts = Posts.objects.filter(author__in=sub)
        comments = Comment.objects.filter(post__in=posts)
        context['posts'] = posts
        context['comments'] = comments
        context['selected'] = 2
        return context

    def post(self, request):
        form = self.form_class(request.POST)
        # button_value = request.POST.get('sub')
        
        if form.is_valid():
            form.instance.author = self.request.user
            form.save()
        
        return redirect('lenta')
    
    

class ShowSubs(LoginRequiredMixin, ListView):
    model = Subscription
    template_name = 'storage/subs.html'
    context_object_name = 'subs'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Подписки'
        return context
    
    def get_queryset(self):
        queryset = Subscription.objects.filter(subscriber=self.request.user)
        return queryset
    
    
class Subscribers(LoginRequiredMixin, ListView):
    model = Subscription
    template_name = 'storage/subscribers.html'
    context_object_name = 'subs'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Подписчики'
        return context
    
    def get_queryset(self):
        queryset = Subscription.objects.filter(subscriberTo=self.request.user)
        return queryset
    