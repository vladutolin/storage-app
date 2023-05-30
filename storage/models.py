from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import os


def user_directory_path(instance, filename):
    # получаем имя пользователя из поля модели
    username = instance.owner.username
    # формируем путь до директории пользователя
    return os.path.join('uploads', username, filename)

        
class File(models.Model):
    owner = models.ForeignKey(User,on_delete=models.CASCADE)
    file = models.FileField(upload_to=user_directory_path)
    time_create = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    time_update = models.DateTimeField(auto_now=True, verbose_name='Дата изменения')
    folder = models.ForeignKey('Folder', on_delete=models.CASCADE, null=True)
    
    # def __str__(self):
    #     ind = self.file.name.rfind('/')
    #     return self.file.name[ind+1:]
    
    def filename(self):
        ind = self.file.name.rfind('/')
        return self.file.name[ind+1:] 
    
    def get_absolute_url(self):
        return reverse('file', kwargs={'file_id': self.pk},)
    

class Folder(models.Model):
    name = models.CharField(max_length=255)
    path = models.CharField(max_length=255)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    time_create = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    time_update = models.DateTimeField(auto_now=True, verbose_name='Дата изменения')
    owner = models.ForeignKey(User,on_delete=models.CASCADE)
    
    def save(self, *args, **kwargs):
        if not self.id:
            if self.parent:
                self.path = self.parent.path + '/' + self.name
            else:
                self.path = self.name
                
        if Folder.objects.filter(parent=self.parent, path=self.path, owner=self.owner).exists():
            raise ValidationError("Папка с таким названием уже существует в родительской папке.")
        super(Folder, self).save(*args, **kwargs)
    
    def get_absolute_url(self):

        return reverse('folder', kwargs={'folder_path': self.path},)
    
    
class Subscription(models.Model):
    subscriber = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subs')
    subscriberTo = models.ForeignKey(User, on_delete=models.CASCADE)
    
class Posts(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    time_create = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    time_update = models.DateTimeField(auto_now=True, verbose_name='Дата изменения')
    desc = models.CharField(max_length=400)
    file = models.ForeignKey(File, on_delete=models.CASCADE)


class Comment(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    time_create = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    text = models.CharField(max_length=400)
    post = models.ForeignKey(Posts, on_delete=models.CASCADE)
