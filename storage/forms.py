from django import forms
from .models import *
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.db import IntegrityError

class RegisterUserForm(UserCreationForm):
    username = forms.CharField(label='Логин', widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Введите логин'}))
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Введите почту'}))
    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Введите пароль'}))
    password2 = forms.CharField(label='Повторите Пароль', widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Введите пароль'}))

    
    class Meta:
        model = User
        fields = ('username', 'email','password1', 'password2')
        
    def clean_email(self):
       email = self.cleaned_data.get('email')
       if User.objects.filter(email=email).exists():
            raise ValidationError("Email exists")
       return email
   
   
class LoginUserForm(AuthenticationForm):
    username = forms.CharField(label='Логин', widget=forms.TextInput(attrs={'class': 'form-input' , 'placeholder': 'Введите логин'}))
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Введите пароль'}))


class AddFileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].label = 'Загрузить файл' 
        
        
    class Meta:
        model = File
        fields = ['file']

class AddFolderForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].label = 'Создать папку' 
        self.fields['name'].widget.attrs.update({'class': 'form-input', 'placeholder': 'Название папки'})
        
    class Meta:
        model = Folder
        fields = ['name']
        
    def clean_path(self):
       path = self.cleaned_data.get('path')
       if Folder.objects.filter(path=path).exists():
            raise IntegrityError("Уже есть ")
       return path
   
class AddPostsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(AddPostsForm, self).__init__(*args, **kwargs)
        self.fields['file'].queryset = File.objects.filter(owner=user)  
        
        
    class Meta:
        model = Posts
        fields = ['desc', 'file']
        widgets = {
            'desc': forms.Textarea(attrs={'rows': 3}),
            'file': forms.Select(attrs={'class': 'form-control'})
        }


class EditProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        
        
class AddComment(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3}),
        }
