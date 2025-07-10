from django.contrib.auth import views as auth_views
from .views import register_view, custom_login_view, logout_view

from django.urls import path

urlpatterns = [
    path('login/', custom_login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),
]