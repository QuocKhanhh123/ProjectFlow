from .views import view_projects, view_frame
from django.urls import path

urlpatterns = [
    path('projects/', view_projects, name='view_projects'),
    path('frame/', view_frame, name=' view_frame'),
]