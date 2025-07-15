from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Project, Task, ProjectStatus, Comment
from .forms import ProjectForm


@login_required(login_url="login")
def view_overview(request):
    return render(request, 'dashboard/overview.html')

@login_required(login_url="login")
def view_projects(request):
    user = request.user
    projects = Project.objects.filter(owner=user).order_by('-created_at')
    
    total_projects = projects.count()
    active_projects = projects.filter(status='ACTIVE').count()
    completed_projects = projects.filter(status='COMPLETED').count()
    on_hold_projects = projects.filter(status='ON_HOLD').count()
    
    context = {
        'username': user.username,
        'projects': projects,
        'total_projects': total_projects,
        'active_projects': active_projects,
        'completed_projects': completed_projects,
        'on_hold_projects': on_hold_projects,
    }
    print(context)  # Debugging line to check context

    return render(request, 'dashboard/projects_content.html', context)


@login_required(login_url="login")
def create_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            messages.success(request, 'Dự án đã được tạo thành công!')
            return redirect('view_projects')
        else:
            messages.error(request, 'Có lỗi xảy ra khi tạo dự án. Vui lòng kiểm tra lại thông tin.')
    else:
        form = ProjectForm()
    
    context = {
        'form': form,
        'title': 'Tạo dự án mới'
    }
    return render(request, 'dashboard/create_project.html', context)

@login_required(login_url="login")
def edit_project(request, project_id):
    project = get_object_or_404(Project, id=project_id, owner=request.user)
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, 'Dự án đã được cập nhật thành công!')
            return redirect('view_projects')
        else:
            messages.error(request, 'Có lỗi xảy ra khi cập nhật dự án.')
    else:
        form = ProjectForm(instance=project)
    
    context = {
        'form': form,
        'project': project,
        'title': 'Chỉnh sửa dự án'
    }
    return render(request, 'dashboard/create_project.html', context)

@login_required(login_url="login")
def delete_project(request, project_id):
    project = get_object_or_404(Project, id=project_id, owner=request.user)
    
    if request.method == 'POST':
        project.delete()
        messages.success(request, 'Dự án đã được xóa thành công!')
        return redirect('view_projects')
    
    context = {
        'project': project
    }
    return render(request, 'dashboard/delete_project.html', context)

@login_required(login_url="login")
def view_project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id, owner=request.user)
    tasks = Task.objects.filter(project=project).order_by('-created_at')
    context = {
        'project': project,
        "tasks": tasks,
    }
    print(context)  # Debugging line to check context
    return render(request, 'dashboard/project_detail.html', context)


@login_required(login_url="login")
def view_project_id(request):
    return render(request, 'dashboard/tasks.html')

@login_required(login_url="login")
def view_project_members(request):
    return render(request, 'dashboard/members.html')

@login_required(login_url="login")
def view_project_task_id(request):
    
    return render(request, 'dashboard/task_detail.html')

@login_required(login_url="login")
def view_profile(request):
    return render(request, 'dashboard/personal_details.html')

@login_required(login_url="login")
def view_settings(request):
    return render(request, 'dashboard/settings.html')

def home(request):
    return render(request, 'base.html')

def view_frame(request):
    return render(request, 'dashboard/frame.html')
