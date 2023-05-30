from django.urls import path
 
from .views import *
 
urlpatterns = [
    path('', Home.as_view(), name='home'),
    path('register/', RegisterUser.as_view(),name='register'),
    path('login/', LoginUser.as_view(),name='login'),
    path('logout/', logout_user, name='logout'),
    path('disk/', Disk.as_view(),name='disk'),
    path('file/<int:file_id>/', show_file, name='file'),
    path('disk/<path:folder_path>/', DiskFolder.as_view(), name='folder'),
    path('file/<int:pk>/delete/', DeleteFile.as_view(), name='delete_file'),
    path('folder/<int:pk>/delete/', DeleteFolder.as_view(), name='delete_folder'),
    path('profile/', Profile.as_view(), name='profile'),
    path('editprofile/', EditProfile.as_view(), name='editprofile'),
    path('profile/<str:username>/', UserProfile.as_view(), name='user_profile'),
    path('add_comment/<int:post_id>/', add_comment, name='add_comment'),
    path('plus_sub/<str:username>/', plus_sub, name='plus_sub'),
    path('minus_sub/<str:username>/', minus_sub, name='minus_sub'),
    path('lenta/', Lenta.as_view(), name='lenta'),
]