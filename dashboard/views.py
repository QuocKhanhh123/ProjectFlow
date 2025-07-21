from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
import json
from .models import Project, Task, ProjectStatus, Comment, ProjectMember, ProjectInvitation, MemberRole, InvitationStatus
from .forms import ProjectForm
from users.models import User


def get_user_project_access(user, project):
    """
    Helper function to check if user has access to project and return their member record.
    Automatically creates ProjectMember record for project owner if it doesn't exist.
    """
    if project.owner == user:
        
        user_member, created = ProjectMember.objects.get_or_create(
            user=user,
            project=project,
            defaults={'role': MemberRole.OWNER}
        )
        return user_member
    else:
        
        return ProjectMember.objects.filter(user=user, project=project).first()


@login_required(login_url="login")
def view_overview(request):
    user = request.user
    
    
    owned_projects = Project.objects.filter(owner=user)
    member_projects = ProjectMember.objects.filter(user=user).select_related('project')
    
    
    all_project_ids = set()
    all_projects = []
    
    
    for project in owned_projects:
        all_project_ids.add(project.id)
        all_projects.append(project)
    
    
    for member_project in member_projects:
        project = member_project.project
        if project.id not in all_project_ids:
            all_project_ids.add(project.id)
            all_projects.append(project)
    
    
    total_projects = len(all_projects)
    owned_count = owned_projects.count()
    member_count = total_projects - owned_count
    
    
    active_projects = len([p for p in all_projects if p.status == 'ACTIVE'])
    completed_projects = len([p for p in all_projects if p.status == 'COMPLETED'])
    on_hold_projects = len([p for p in all_projects if p.status == 'ON_HOLD'])
    
    
    all_tasks = Task.objects.filter(project__in=all_projects)
    total_tasks = all_tasks.count()
    todo_tasks = all_tasks.filter(status='TODO').count()
    in_progress_tasks = all_tasks.filter(status='IN_PROGRESS').count()
    done_tasks = all_tasks.filter(status='DONE').count()
    
    
    my_tasks = all_tasks.filter(assignee=user)
    my_total_tasks = my_tasks.count()
    my_todo_tasks = my_tasks.filter(status='TODO').count()
    my_in_progress_tasks = my_tasks.filter(status='IN_PROGRESS').count()
    my_done_tasks = my_tasks.filter(status='DONE').count()
    
    
    high_priority_tasks = all_tasks.filter(priority='HIGH').count()
    medium_priority_tasks = all_tasks.filter(priority='MEDIUM').count()
    low_priority_tasks = all_tasks.filter(priority='LOW').count()
    
    
    seven_days_ago = timezone.now() - timedelta(days=7)
    recent_tasks = all_tasks.filter(created_at__gte=seven_days_ago).count()
    recent_comments = Comment.objects.filter(
        task__project__in=all_projects,
        created_at__gte=seven_days_ago
    ).count()
    
    
    total_members = ProjectMember.objects.filter(project__in=all_projects).count()
    active_members = ProjectMember.objects.filter(
        project__in=all_projects,
        user__tasks__updated_at__gte=seven_days_ago
    ).distinct().count()
    
    
    recent_projects = sorted(all_projects, key=lambda x: x.created_at, reverse=True)[:5]
    
    
    project_progress = []
    for project in all_projects:
        project_tasks = Task.objects.filter(project=project)
        total_project_tasks = project_tasks.count()
        completed_project_tasks = project_tasks.filter(status='DONE').count()
        
        if total_project_tasks > 0:
            progress = (completed_project_tasks / total_project_tasks) * 100
        else:
            progress = 0
            
        project_progress.append({
            'project': project,
            'progress': round(progress, 1),
            'total_tasks': total_project_tasks,
            'completed_tasks': completed_project_tasks
        })
    
    
    chart_data = {
        'project_status': {
            'active': active_projects,
            'completed': completed_projects,
            'on_hold': on_hold_projects
        },
        'task_status': {
            'todo': todo_tasks,
            'in_progress': in_progress_tasks,
            'done': done_tasks
        },
        'task_priority': {
            'high': high_priority_tasks,
            'medium': medium_priority_tasks,
            'low': low_priority_tasks
        },
        'my_tasks': {
            'todo': my_todo_tasks,
            'in_progress': my_in_progress_tasks,
            'done': my_done_tasks
        }
    }
    
    context = {
        'user': user,
        'total_projects': total_projects,
        'owned_count': owned_count,
        'member_count': member_count,
        'active_projects': active_projects,
        'completed_projects': completed_projects,
        'on_hold_projects': on_hold_projects,
        'total_tasks': total_tasks,
        'todo_tasks': todo_tasks,
        'in_progress_tasks': in_progress_tasks,
        'done_tasks': done_tasks,
        'my_total_tasks': my_total_tasks,
        'my_todo_tasks': my_todo_tasks,
        'my_in_progress_tasks': my_in_progress_tasks,
        'my_done_tasks': my_done_tasks,
        'high_priority_tasks': high_priority_tasks,
        'medium_priority_tasks': medium_priority_tasks,
        'low_priority_tasks': low_priority_tasks,
        'recent_tasks': recent_tasks,
        'recent_comments': recent_comments,
        'total_members': total_members,
        'active_members': active_members,
        'recent_projects': recent_projects,
        'project_progress': project_progress,
        'chart_data': chart_data
    }
    
    return render(request, 'dashboard/overview.html', context)

@login_required(login_url="login")
def view_projects(request):
    user = request.user
    
    owned_projects = Project.objects.filter(owner=user)
    
    member_projects = ProjectMember.objects.filter(user=user).select_related('project')
    
    
    all_project_ids = set()
    projects_data = []
    
    
    for project in owned_projects:
        if project.id not in all_project_ids:
            all_project_ids.add(project.id)
            
            member_role = ProjectMember.objects.filter(user=user, project=project).first()
            user_role = member_role.role if member_role else 'OWNER'
            
            projects_data.append({
                'project': project,
                'user_role': user_role,
                'is_owner': True
            })
    
    
    for member_project in member_projects:
        project = member_project.project
        if project.id not in all_project_ids:
            all_project_ids.add(project.id)
            projects_data.append({
                'project': project,
                'user_role': member_project.role,
                'is_owner': project.owner == user
            })
    
    
    projects_data.sort(key=lambda x: x['project'].created_at, reverse=True)
    
    
    total_projects = len(projects_data)
    owned_projects_count = len([p for p in projects_data if p['is_owner']])
    member_projects_count = len([p for p in projects_data if not p['is_owner']])
    
    
    active_projects = len([p for p in projects_data if p['project'].status == 'ACTIVE'])
    completed_projects = len([p for p in projects_data if p['project'].status == 'COMPLETED'])
    on_hold_projects = len([p for p in projects_data if p['project'].status == 'ON_HOLD'])
    
    context = {
        'username': user.username,
        'projects_data': projects_data,
        'total_projects': total_projects,
        'owned_projects_count': owned_projects_count,
        'member_projects_count': member_projects_count,
        'active_projects': active_projects,
        'completed_projects': completed_projects,
        'on_hold_projects': on_hold_projects,
    }


    return render(request, 'dashboard/projects_content.html', context)


@login_required(login_url="login")
def create_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            
            
            ProjectMember.objects.create(
                user=request.user,
                project=project,
                role=MemberRole.OWNER
            )
            
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
    
    project = get_object_or_404(Project, id=project_id)
    user_member = get_user_project_access(request.user, project)
    
    if not user_member:
        messages.error(request, 'Bạn không có quyền truy cập dự án này.')
        return redirect('view_projects')
    
    tasks = Task.objects.filter(project=project).order_by('-created_at')
    
    
    todo_count = tasks.filter(status='TODO').count()
    in_progress_count = tasks.filter(status='IN_PROGRESS').count()
    done_count = tasks.filter(status='DONE').count()
    
    members = project.members.select_related('user').all()
    context = {
        'project': project,
        'tasks': tasks,
        'todo_count': todo_count,
        'in_progress_count': in_progress_count,
        'done_count': done_count,
        'user_role': user_member.role,
        'can_edit': user_member.role in [MemberRole.OWNER, MemberRole.ADMIN],
        'members': members,
    }
    return render(request, 'dashboard/project_detail.html', context)

@login_required(login_url="login")
@require_http_methods(["POST"])
def create_task(request, project_id):
    try:
        
        project = get_object_or_404(Project, id=project_id)
        user_member = get_user_project_access(request.user, project)
        
        if not user_member:
            return JsonResponse({
                'success': False,
                'error': 'Bạn không có quyền truy cập dự án này'
            }, status=403)
        
        
        data = json.loads(request.body)
        
        
        title = data.get('title', '').strip()
        if not title:
            return JsonResponse({
                'success': False,
                'error': 'Tiêu đề là bắt buộc'
            }, status=400)
        
        description = data.get('description', '').strip()
        status = data.get('status', 'TODO')
        priority = data.get('priority', 'MEDIUM')
        
        
        valid_statuses = ['TODO', 'IN_PROGRESS', 'DONE']
        valid_priorities = ['LOW', 'MEDIUM', 'HIGH']
        
        if status not in valid_statuses:
            status = 'TODO'
        if priority not in valid_priorities:
            priority = 'MEDIUM'
        
        
        task = Task.objects.create(
            title=title,
            description=description,
            status=status,
            priority=priority,
            project=project,
            assignee=request.user  
        )
        
        return JsonResponse({
            'success': True,
            'task': {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'status': task.status,
                'priority': task.priority,
                'created_at': task.created_at.isoformat(),
                'assignee': task.assignee.username if task.assignee else None
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Dữ liệu JSON không hợp lệ'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Đã xảy ra lỗi: {str(e)}'
        }, status=500)



@login_required(login_url="login")
def view_project_id(request):
    return render(request, 'dashboard/tasks.html')

@login_required(login_url="login")
def view_project_members(request, project_id):
    
    project = get_object_or_404(Project, id=project_id)
    user_member = get_user_project_access(request.user, project)
    
    if not user_member:
        messages.error(request, 'Bạn không có quyền truy cập dự án này.')
        return redirect('view_projects')
    
    if user_member.role not in [MemberRole.OWNER, MemberRole.ADMIN]:
        messages.error(request, 'Bạn không có quyền quản lý thành viên dự án này.')
        return redirect('view_project_detail', project_id=project_id)
    
    
    members = ProjectMember.objects.filter(project=project).select_related('user').order_by('-joined_at')
    
    
    member_stats = []
    for member in members:
        try:
            
            assigned_tasks = Task.objects.filter(project=project, assignee=member.user).count()
            completed_tasks = Task.objects.filter(project=project, assignee=member.user, status='DONE').count()
            
            
            comments_count = Comment.objects.filter(user=member.user, task__project=project).count()
            
            
            thirty_days_ago = timezone.now() - timedelta(days=30)
            is_active = (
                Task.objects.filter(assignee=member.user, updated_at__gte=thirty_days_ago, project=project).exists() or
                Comment.objects.filter(user=member.user, created_at__gte=thirty_days_ago, task__project=project).exists()
            )
            
            
            last_task_activity = Task.objects.filter(assignee=member.user, project=project).order_by('-updated_at').first()
            last_comment_activity = Comment.objects.filter(user=member.user, task__project=project).order_by('-created_at').first()
            
            last_activity = None
            if last_task_activity and last_comment_activity:
                last_activity = max(last_task_activity.updated_at, last_comment_activity.created_at)
            elif last_task_activity:
                last_activity = last_task_activity.updated_at
            elif last_comment_activity:
                last_activity = last_comment_activity.created_at
            
            completion_rate = round((completed_tasks / assigned_tasks * 100) if assigned_tasks > 0 else 0, 1)
            
            member_stat = {
                'member': member,
                'assigned_tasks': assigned_tasks,
                'completed_tasks': completed_tasks,
                'comments_count': comments_count,
                'is_active': is_active,
                'last_activity': last_activity,
                'completion_rate': completion_rate
            }
            
            member_stats.append(member_stat)
            
        except Exception as e:
            
            member_stats.append({
                'member': member,
                'assigned_tasks': 0,
                'completed_tasks': 0,
                'comments_count': 0,
                'is_active': False,
                'last_activity': None,
                'completion_rate': 0
            })
    
    
    pending_invitations = ProjectInvitation.objects.filter(
        project=project, 
        status=InvitationStatus.PENDING
    ).order_by('-sent_at')
    
    
    total_members = members.count()
    admin_count = members.filter(role__in=[MemberRole.OWNER, MemberRole.ADMIN]).count()
    pending_count = pending_invitations.count()
    
    
    active_members = sum(1 for stat in member_stats if stat['is_active'])
    
    
    total_project_tasks = Task.objects.filter(project=project).count()
    completed_project_tasks = Task.objects.filter(project=project, status='DONE').count()
    project_progress = round((completed_project_tasks / total_project_tasks * 100) if total_project_tasks > 0 else 0, 1)
    
    
    recent_tasks = Task.objects.filter(project=project).order_by('-created_at')[:5]
    recent_comments = Comment.objects.filter(task__project=project).select_related('user', 'task').order_by('-created_at')[:5]
    
    context = {
        'project': project,
        'members': members,
        'member_stats': member_stats,
        'pending_invitations': pending_invitations,
        'total_members': total_members,
        'admin_count': admin_count,
        'pending_count': pending_count,
        'active_members': active_members,
        'user_role': user_member.role,
        'total_project_tasks': total_project_tasks,
        'completed_project_tasks': completed_project_tasks,
        'project_progress': project_progress,
        'recent_tasks': recent_tasks,
        'recent_comments': recent_comments,
    }
    
    return render(request, 'dashboard/members.html', context)

@login_required(login_url="login")
def view_project_task_id(request, project_id, task_id):
    
    project = get_object_or_404(Project, id=project_id)
    user_member = get_user_project_access(request.user, project)
    
    if not user_member:
        messages.error(request, 'Bạn không có quyền truy cập dự án này.')
        return redirect('view_projects')
    
    task = get_object_or_404(Task, id=task_id, project=project)
    comments = Comment.objects.filter(task=task).order_by('created_at')
    
    context = {
        'project': project,
        'task': task,
        'comments': comments,
        'user_role': user_member.role,
        'can_edit': user_member.role in [MemberRole.OWNER, MemberRole.ADMIN]
    }
    return render(request, 'dashboard/task_detail.html', context)

@login_required(login_url="login")
@require_http_methods(["PUT"])
def update_task(request, project_id, task_id):
    try:
        
        project = get_object_or_404(Project, id=project_id)
        user_member = get_user_project_access(request.user, project)
        
        if not user_member:
            return JsonResponse({
                'success': False,
                'error': 'Bạn không có quyền truy cập dự án này'
            }, status=403)
        
        task = get_object_or_404(Task, id=task_id, project=project)
        
        
        data = json.loads(request.body)
        
        
        title = data.get('title', '').strip()
        if not title:
            return JsonResponse({
                'success': False,
                'error': 'Tiêu đề là bắt buộc'
            }, status=400)
        
        description = data.get('description', '').strip()
        status = data.get('status', task.status)
        priority = data.get('priority', task.priority)
        
        
        valid_statuses = ['TODO', 'IN_PROGRESS', 'DONE']
        valid_priorities = ['LOW', 'MEDIUM', 'HIGH']
        
        if status not in valid_statuses:
            status = task.status
        if priority not in valid_priorities:
            priority = task.priority
        
        
        task.title = title
        task.description = description
        task.status = status
        task.priority = priority
        task.save()
        
        return JsonResponse({
            'success': True,
            'task': {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'status': task.status,
                'priority': task.priority,
                'updated_at': task.updated_at.isoformat(),
                'assignee': task.assignee.username if task.assignee else None
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Dữ liệu JSON không hợp lệ'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Đã xảy ra lỗi: {str(e)}'
        }, status=500)

@login_required(login_url="login")
@require_http_methods(["POST"])
def create_comment(request, project_id, task_id):
    try:
        
        project = get_object_or_404(Project, id=project_id)
        user_member = get_user_project_access(request.user, project)
        
        if not user_member:
            return JsonResponse({
                'success': False,
                'error': 'Bạn không có quyền truy cập dự án này'
            }, status=403)
        
        task = get_object_or_404(Task, id=task_id, project=project)
        
        
        data = json.loads(request.body)
        
        
        content = data.get('content', '').strip()
        if not content:
            return JsonResponse({
                'success': False,
                'error': 'Nội dung comment là bắt buộc'
            }, status=400)
        
        
        comment = Comment.objects.create(
            content=content,
            task=task,
            user=request.user
        )
        
        return JsonResponse({
            'success': True,
            'comment': {
                'id': comment.id,
                'content': comment.content,
                'created_at': comment.created_at.isoformat(),
                'user': {
                    'username': comment.user.username,
                    'id': comment.user.id
                }
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Dữ liệu JSON không hợp lệ'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Đã xảy ra lỗi: {str(e)}'
        }, status=500)

@login_required(login_url="login")
@require_http_methods(["DELETE"])
def delete_task(request, project_id, task_id):
    try:
        
        project = get_object_or_404(Project, id=project_id)
        user_member = get_user_project_access(request.user, project)
        
        if not user_member:
            return JsonResponse({
                'success': False,
                'error': 'Bạn không có quyền truy cập dự án này'
            }, status=403)
        
        
        if user_member.role not in [MemberRole.OWNER, MemberRole.ADMIN]:
            return JsonResponse({
                'success': False,
                'error': 'Bạn không có quyền xóa task trong dự án này'
            }, status=403)
        
        task = get_object_or_404(Task, id=task_id, project=project)
        
        task.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Task đã được xóa thành công'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Đã xảy ra lỗi: {str(e)}'
        }, status=500)

@login_required(login_url="login")
def view_profile(request):
    user = request.user
    
    
    owned_projects = Project.objects.filter(owner=user).count()
    member_projects = ProjectMember.objects.filter(user=user).count()
    assigned_tasks = Task.objects.filter(assignee=user).count()
    completed_tasks = Task.objects.filter(assignee=user, status='DONE').count()
    comments_count = Comment.objects.filter(user=user).count()
    
    
    recent_tasks = Task.objects.filter(assignee=user).order_by('-updated_at')[:5]
    recent_comments = Comment.objects.filter(user=user).order_by('-created_at')[:5]
    
    context = {
        'user': user,
        'owned_projects': owned_projects,
        'member_projects': member_projects,
        'assigned_tasks': assigned_tasks,
        'completed_tasks': completed_tasks,
        'comments_count': comments_count,
        'recent_tasks': recent_tasks,
        'recent_comments': recent_comments
    }
    
    return render(request, 'dashboard/personal_details.html', context)

@login_required(login_url="login")
def view_settings(request):
    return render(request, 'dashboard/settings.html')

def home(request):
    return render(request, 'base.html')

def view_frame(request):
    return render(request, 'dashboard/frame.html')

@login_required(login_url="login")
@require_http_methods(["POST"])
def invite_member(request, project_id):
    try:
        
        project = get_object_or_404(Project, id=project_id)
        user_member = get_user_project_access(request.user, project)
        
        if not user_member:
            return JsonResponse({
                'success': False,
                'error': 'Bạn không có quyền truy cập dự án này'
            }, status=403)
        
        if user_member.role not in [MemberRole.OWNER, MemberRole.ADMIN]:
            return JsonResponse({
                'success': False,
                'error': 'Bạn không có quyền thêm thành viên vào dự án này'
            }, status=403)
        
        
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        role = data.get('role', MemberRole.MEMBER)
        
        if not email:
            return JsonResponse({
                'success': False,
                'error': 'Email là bắt buộc'
            }, status=400)
        
        
        if role not in [choice[0] for choice in MemberRole.choices]:
            role = MemberRole.MEMBER
        
        
        try:
            user = User.objects.filter(email=email).first()
            if not user:
                return JsonResponse({
                    'success': False,
                    'error': 'Không tìm thấy người dùng với email này'
                }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Lỗi khi tìm người dùng: {str(e)}'
            }, status=500)
        
        
        if ProjectMember.objects.filter(user=user, project=project).exists():
            return JsonResponse({
                'success': False,
                'error': 'Người dùng đã là thành viên của dự án'
            }, status=400)
        
        
        member = ProjectMember.objects.create(
            user=user,
            project=project,
            role=role
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Đã thêm {user.username} vào dự án thành công',
            'member': {
                'id': member.id,
                'username': user.username,
                'email': user.email,
                'role': member.role,
                'joined_at': member.joined_at.isoformat()
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Dữ liệu JSON không hợp lệ'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Đã xảy ra lỗi: {str(e)}'
        }, status=500)

@login_required(login_url="login")
@require_http_methods(["POST"])
def accept_invitation(request, invitation_id):
    try:
        invitation = get_object_or_404(
            ProjectInvitation, 
            id=invitation_id,
            receiver_email=request.user.email,
            status=InvitationStatus.PENDING
        )
        
        
        if invitation.expires_at < timezone.now():
            invitation.status = InvitationStatus.EXPIRED
            invitation.save()
            return JsonResponse({
                'success': False,
                'error': 'Lời mời đã hết hạn'
            }, status=400)
        
        
        if ProjectMember.objects.filter(user=request.user, project=invitation.project).exists():
            return JsonResponse({
                'success': False,
                'error': 'Bạn đã là thành viên của dự án'
            }, status=400)
        
        
        invitation.status = InvitationStatus.ACCEPTED
        invitation.save()
        
        
        ProjectMember.objects.create(
            user=request.user,
            project=invitation.project,
            role=invitation.role
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Lời mời đã được chấp nhận thành công'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Đã xảy ra lỗi: {str(e)}'
        }, status=500)

@login_required(login_url="login")
@require_http_methods(["POST"])
def decline_invitation(request, invitation_id):
    try:
        invitation = get_object_or_404(
            ProjectInvitation, 
            id=invitation_id,
            receiver_email=request.user.email,
            status=InvitationStatus.PENDING
        )
        
        invitation.status = InvitationStatus.DECLINED
        invitation.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Lời mời đã được từ chối'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Đã xảy ra lỗi: {str(e)}'
        }, status=500)

@login_required(login_url="login")
@require_http_methods(["POST"])
def remove_member(request, project_id, member_id):
    try:
        
        project = get_object_or_404(Project, id=project_id)
        user_member = get_user_project_access(request.user, project)
        
        if not user_member:
            return JsonResponse({
                'success': False,
                'error': 'Bạn không có quyền truy cập dự án này'
            }, status=403)
        
        if user_member.role not in [MemberRole.OWNER, MemberRole.ADMIN]:
            return JsonResponse({
                'success': False,
                'error': 'Bạn không có quyền xóa thành viên khỏi dự án này'
            }, status=403)
        
        member = get_object_or_404(ProjectMember, id=member_id, project=project)
        
        
        if member.role == MemberRole.OWNER:
            return JsonResponse({
                'success': False,
                'error': 'Không thể xóa chủ sở hữu dự án'
            }, status=400)
        
        
        member_info = {
            'username': member.user.username,
            'email': member.user.email
        }
        
        member.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Đã xóa thành viên {member_info["username"]} khỏi dự án'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Đã xảy ra lỗi: {str(e)}'
        }, status=500)

@login_required(login_url="login")
@require_http_methods(["POST"])
def update_member_role(request, project_id, member_id):
    try:
        
        project = get_object_or_404(Project, id=project_id)
        user_member = get_user_project_access(request.user, project)
        
        if not user_member:
            return JsonResponse({
                'success': False,
                'error': 'Bạn không có quyền truy cập dự án này'
            }, status=403)
        
        if user_member.role not in [MemberRole.OWNER, MemberRole.ADMIN]:
            return JsonResponse({
                'success': False,
                'error': 'Bạn không có quyền cập nhật vai trò thành viên'
            }, status=403)
        
        member = get_object_or_404(ProjectMember, id=member_id, project=project)
        
        
        if member.role == MemberRole.OWNER:
            return JsonResponse({
                'success': False,
                'error': 'Không thể thay đổi vai trò của chủ sở hữu dự án'
            }, status=400)
        
        
        data = json.loads(request.body)
        new_role = data.get('role', member.role)
        
        
        if new_role == MemberRole.OWNER:
            return JsonResponse({
                'success': False,
                'error': 'Không thể chỉ định vai trò chủ sở hữu'
            }, status=400)
        
        if new_role not in [MemberRole.ADMIN, MemberRole.MEMBER]:
            return JsonResponse({
                'success': False,
                'error': 'Vai trò không hợp lệ'
            }, status=400)
        
        member.role = new_role
        member.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Đã cập nhật vai trò thành viên thành {new_role}',
            'member': {
                'id': member.id,
                'username': member.user.username,
                'role': member.role
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Dữ liệu JSON không hợp lệ'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Đã xảy ra lỗi: {str(e)}'
        }, status=500)

@login_required(login_url="login")
@require_http_methods(["DELETE"])
def cancel_invitation(request, project_id, invitation_id):
    try:
        project = get_object_or_404(Project, id=project_id, owner=request.user)
        invitation = get_object_or_404(
            ProjectInvitation, 
            id=invitation_id, 
            project=project,
            status=InvitationStatus.PENDING
        )
        
        invitation.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Lời mời đã được hủy'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Đã xảy ra lỗi: {str(e)}'
        }, status=500)

@login_required(login_url="login")
def view_all_members(request):
    """View to show all projects where user is a member"""
    user = request.user
    
    
    member_projects = ProjectMember.objects.filter(user=user).select_related('project').order_by('-joined_at')
    
    projects_data = []
    owner_count = 0
    admin_count = 0
    member_count = 0
    
    for member_project in member_projects:
        project = member_project.project
        members_count = ProjectMember.objects.filter(project=project).count()
        pending_invitations = ProjectInvitation.objects.filter(
            project=project, 
            status=InvitationStatus.PENDING
        ).count()
        
        
        if member_project.role == MemberRole.OWNER:
            owner_count += 1
        elif member_project.role == MemberRole.ADMIN:
            admin_count += 1
        else:
            member_count += 1
        
        projects_data.append({
            'project': project,
            'user_role': member_project.role,
            'members_count': members_count,
            'pending_invitations': pending_invitations,
            'joined_at': member_project.joined_at
        })
    
    context = {
        'projects_data': projects_data,
        'total_projects': len(projects_data),
        'owner_count': owner_count,
        'admin_count': admin_count,
        'member_count': member_count
    }
    
    return render(request, 'dashboard/all_members.html', context)

@login_required(login_url="login")
@require_http_methods(["POST"])
def update_profile(request):
    try:
        
        data = json.loads(request.body)
        
        
        user = request.user
        
        
        new_username = data.get('username', user.username)
        new_email = data.get('email', user.email)
        new_first_name = data.get('first_name', user.first_name)
        new_last_name = data.get('last_name', user.last_name)
        
        
        if new_email != user.email:
            if User.objects.filter(email=new_email).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Email này đã được sử dụng bởi người khác'
                }, status=400)
        
        
        if new_username != user.username:
            if User.objects.filter(username=new_username).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Tên đăng nhập này đã được sử dụng bởi người khác'
                }, status=400)
        
        
        user.username = new_username
        user.email = new_email
        user.first_name = new_first_name
        user.last_name = new_last_name
        user.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Cập nhật thông tin cá nhân thành công',
            'user': {
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Dữ liệu JSON không hợp lệ'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Đã xảy ra lỗi: {str(e)}'
        }, status=500)

@login_required(login_url="login")
@require_http_methods(["POST"])
def change_password(request):
    try:
        
        data = json.loads(request.body)
        
        old_password = data.get('old_password', '')
        new_password1 = data.get('new_password1', '')
        new_password2 = data.get('new_password2', '')
        
        
        if not request.user.check_password(old_password):
            return JsonResponse({
                'success': False,
                'error': 'Mật khẩu hiện tại không đúng'
            }, status=400)
        
        
        if len(new_password1) < 4:
            return JsonResponse({
                'success': False,
                'error': 'Mật khẩu mới phải có ít nhất 4 ký tự'
            }, status=400)
        
        
        if new_password1 != new_password2:
            return JsonResponse({
                'success': False,
                'error': 'Mật khẩu mới và xác nhận mật khẩu không khớp'
            }, status=400)
        
        
        request.user.set_password(new_password1)
        request.user.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Đổi mật khẩu thành công'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Dữ liệu JSON không hợp lệ'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Đã xảy ra lỗi: {str(e)}'
        }, status=500)

@login_required(login_url="login")
def search_view(request):
    """
    Search view để tìm kiếm dự án và công việc
    """
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({
            'success': False,
            'error': 'Vui lòng nhập từ khóa tìm kiếm'
        })
    
    user = request.user
    
    
    user_projects = []
    
    
    owned_projects = Project.objects.filter(owner=user)
    user_projects.extend(owned_projects)
    
    
    member_projects = ProjectMember.objects.filter(user=user).select_related('project')
    for member_project in member_projects:
        if member_project.project not in user_projects:
            user_projects.append(member_project.project)
    
    
    project_ids = [p.id for p in user_projects]
    projects = Project.objects.filter(
        id__in=project_ids
    ).filter(
        Q(name__icontains=query) | Q(description__icontains=query)
    ).order_by('-created_at')[:10]
    
    
    tasks = Task.objects.filter(
        project__id__in=project_ids
    ).filter(
        Q(title__icontains=query) | Q(description__icontains=query)
    ).select_related('project').order_by('-created_at')[:10]
    
    
    projects_data = []
    for project in projects:
        projects_data.append({
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'status': project.status,
            'created_at': project.created_at.isoformat(),
        })
    
    tasks_data = []
    for task in tasks:
        tasks_data.append({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'status': task.status,
            'priority': task.priority,
            'project_id': task.project.id,
            'project_name': task.project.name,
            'created_at': task.created_at.isoformat(),
        })
    
    return JsonResponse({
        'success': True,
        'results': {
            'projects': projects_data,
            'tasks': tasks_data
        },
        'query': query
    })
