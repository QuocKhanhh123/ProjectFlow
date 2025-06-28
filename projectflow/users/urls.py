from django.contrib.auth import views as auth_views
from .views import register_view, custom_login_view

from django.urls import path

urlpatterns = [
    path('login/', custom_login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', register_view, name='register'),
]