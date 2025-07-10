from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import Project

@login_required(login_url="login")
def view_projects(request):
    user = request.user.username
    context = {
        'username': user,
        "projects": [
            {"id": 1, "name": "Project A", "description": "Description of Project A"},
            {"id": 2, "name": "Project B", "description": "Description of Project B"},
            {"id": 3, "name": "Project C", "description": "Description of Project C"},
        ]
    }

    return render(request, 'dashboard/frame.html')

@login_required(login_url="login")
def view_project_id(request):
    return render(request, 'dashboard/tasks.html')


def view_project_members(request):
    return render(request, 'dashboard/members.html')

@login_required(login_url="login")
def view_project_task_id(request):
    return render(request, 'dashboard/task_detail.html')


@login_required(login_url="login")
def view_profile(request):
    return render(request, 'dashboard/profile.html')

def home(request):
    return render(request, 'base.html')

def view_frame(request):
    return render(request, 'dashboard/frame.html')