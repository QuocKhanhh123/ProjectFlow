from .views import view_projects

from django.urls import path

urlpatterns = [
    path('projects/', view_projects, name='view_projects'),
]