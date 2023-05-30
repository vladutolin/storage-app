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

from .models import *
from .forms import *


# Create your views here.


class Home(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('disk')
        context = {
            'title': 'A-Storage'
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
    
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        return super().get(request, *args, **kwargs)
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['upload'] = self.form_class()
        context['new_folder'] = self.form_class_folder()
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
    #success_url = reverse_lazy('disk')
    raise_exception = True
    
    def get(self, request, folder_path):
        # Проверка наличия папки в базе данных
        try:
            folder = Folder.objects.filter(path=folder_path, owner=request.user)[0]
        except Folder.DoesNotExist:
            return HttpResponseForbidden("У вас нет доступа к этой папке.")
        # Проверка владения папкой
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
        return context
    
    # def form_valid(self, form):
    #     form.instance.owner = self.request.user
    #     form.instance.folder = Folder.objects.filter(name=self.kwargs['folder_path'], owner=self.request.user)[0]
    #     print(self.request.path)
    #     return super().form_valid(form)
    
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
        # Получить объект файла
        file_object = self.get_object()

        b = os.path.join(settings.BASE_DIR, 'media')
        # Удалить файл с компьютера
        file_path =os.path.join(b, str(file_object.file))
        print(file_path)
        print(file_path)
        if os.path.exists(file_path):
            os.remove(file_path)
            
        file_object.delete()

        return redirect('disk')
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(owner=self.request.user)
    
class DeleteFolder(LoginRequiredMixin, DeleteView):
    model = Folder
    template_name = 'storage/delete_folder.html'
    success_url = reverse_lazy('disk')
    
    def form_valid(self, request, *args, **kwargs):
        # Получить объект файла
        folder= self.get_object()
        
        file = File.objects.filter(folder=folder)
        b = os.path.join(settings.BASE_DIR, 'media')
        for i in file:
            # Удалить файл с компьютера
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
        return redirect('profile')
    
    def get_queryset(self):
         return Posts.objects.filter(author=self.request.user)
     

class EditProfile(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'storage/editprofile.html'
    success_url = 'profile'
    form_class = EditProfileForm

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
        return context
    
    def post(self, request):
        form = self.form_class(request.POST)
        # button_value = request.POST.get('sub')
        
        if form.is_valid():
            form.instance.author = self.request.user
            form.save()
        
        # if button_value == 'submit':
        #     userTo = User.objects.get(username=self.kwargs['username'])
        #     new_sub = Subscription(subscriber=self.request.user, subscriberTo=userTo)
        #     new_sub.save()
        
        # return redirect(reverse('profile', kwargs={'username': self.kwargs['username']},))
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
    
    return redirect('user_profile', username=post.author.username)


class Lenta(LoginRequiredMixin, ListView):
    model = Posts
    template_name = 'storage/lenta.html'
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
        return context
    
    # def get_queryset(self):
    #     sub = Subscription.objects.filter(subscriber=self.request.user).values_list('subscriberTo', flat=True)
    #     posts = Posts.objects.filter(authot__in=sub)
    #     return posts