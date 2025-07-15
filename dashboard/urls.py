from . import views
from django.urls import path

urlpatterns = [
    path('overview/', views.view_overview, name='view_overview'),
    path('projects/', views.view_projects, name='view_projects'),
    path('projects/create/', views.create_project, name='create_project'),
    path('projects/<int:project_id>/edit/', views.edit_project, name='edit_project'),
    path('projects/<int:project_id>/delete/', views.delete_project, name='delete_project'),
    path('projects/<int:project_id>/', views.view_project_detail, name='view_project_detail'),
    path('frame/', views.view_frame, name='view_frame'),
    path('members/', views.view_project_members, name='view_project_members'),
    path('settings/', views.view_settings, name='view_settings'),
    path('personal/', views.view_profile, name='view_profile'),
]