from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
import json
from .models import Project, Task, ProjectStatus, Comment, ProjectMember, ProjectInvitation, MemberRole, InvitationStatus, TaskCompletionRequest, CompletionRequestStatus, Notification, NotificationType
from .forms import ProjectForm
from .notification_service import NotificationService
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
    
    # Sắp xếp members theo thứ tự role: OWNER -> ADMIN -> LEADER -> MEMBER
    role_order = {
        'OWNER': 1,
        'ADMIN': 2, 
        'LEADER': 3,
        'MEMBER': 4
    }
    members = project.members.select_related('user').all()
    members = sorted(members, key=lambda m: role_order.get(m.role, 5))
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
        deadline = data.get('deadline')
        assignee_id = data.get('assignee_id')
        
        
        valid_statuses = ['TODO', 'IN_PROGRESS', 'DONE']
        valid_priorities = ['LOW', 'MEDIUM', 'HIGH']
        
        if status not in valid_statuses:
            status = 'TODO'
        if priority not in valid_priorities:
            priority = 'MEDIUM'
        
        # Xử lý deadline
        deadline_obj = None
        if deadline:
            try:
                from datetime import datetime
                # Parse datetime từ frontend
                deadline_obj = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                
                # Make timezone aware nếu cần
                if deadline_obj.tzinfo is None:
                    deadline_obj = timezone.make_aware(deadline_obj)
                
                # Validate deadline không được nhỏ hơn thời gian hiện tại
                if deadline_obj <= timezone.now():
                    return JsonResponse({
                        'success': False,
                        'error': 'Hạn hoàn thành phải lớn hơn thời gian hiện tại'
                    }, status=400)
                    
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': 'Định dạng thời gian không hợp lệ'
                }, status=400)
        
        # Xử lý assignee
        assignee = None
        if assignee_id:
            try:
                assignee = User.objects.get(id=assignee_id)
                # Kiểm tra xem user có phải là thành viên của project không
                if not ProjectMember.objects.filter(user=assignee, project=project).exists():
                    return JsonResponse({
                        'success': False,
                        'error': 'Người được giao việc phải là thành viên của dự án'
                    }, status=400)
            except User.DoesNotExist:
                assignee = request.user
        else:
            assignee = request.user
        
        
        task = Task.objects.create(
            title=title,
            description=description,
            status=status,
            priority=priority,
            deadline=deadline_obj,
            project=project,
            assignee=assignee
        )
        
        # Gửi thông báo khi giao việc (nếu có assignee và không phải chính người tạo)
        if assignee and assignee != request.user:
            NotificationService.notify_task_assigned(task, request.user)
        
        return JsonResponse({
            'success': True,
            'task': {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'status': task.status,
                'priority': task.priority,
                'deadline': task.deadline.isoformat() if task.deadline else None,
                'created_at': task.created_at.isoformat(),
                'assignee': task.assignee.username if task.assignee else None,
                'assignee_id': task.assignee.id if task.assignee else None
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
        'can_edit': user_member.role in [MemberRole.OWNER, MemberRole.ADMIN],
        'now': timezone.now()
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
        deadline = data.get('deadline')
        
        
        valid_statuses = ['TODO', 'IN_PROGRESS', 'DONE']
        valid_priorities = ['LOW', 'MEDIUM', 'HIGH']
        
        if status not in valid_statuses:
            status = task.status
        if priority not in valid_priorities:
            priority = task.priority
        
        # Xử lý deadline cho update
        deadline_obj = task.deadline  # Keep existing deadline by default
        if deadline is not None:  # Check for None to allow clearing deadline
            if deadline:  # If not empty string
                try:
                    from datetime import datetime
                    # Parse datetime từ frontend
                    deadline_obj = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                    
                    # Make timezone aware nếu cần
                    if deadline_obj.tzinfo is None:
                        deadline_obj = timezone.make_aware(deadline_obj)
                    
                    # Validate deadline không được nhỏ hơn thời gian hiện tại
                    if deadline_obj <= timezone.now():
                        return JsonResponse({
                            'success': False,
                            'error': 'Hạn hoàn thành phải lớn hơn thời gian hiện tại'
                        }, status=400)
                        
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'error': 'Định dạng thời gian không hợp lệ'
                    }, status=400)
            else:
                deadline_obj = None  # Clear deadline if empty string
        
        
        task.title = title
        task.description = description
        task.status = status
        task.priority = priority
        task.deadline = deadline_obj
        task.save()
        
        return JsonResponse({
            'success': True,
            'task': {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'status': task.status,
                'priority': task.priority,
                'deadline': task.deadline.isoformat() if task.deadline else None,
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

@login_required(login_url="login")
def task_statistics_view(request):
    """
    Hiển thị trang thống kê công việc đang được giao
    """
    return render(request, 'dashboard/task_statistics.html')

@login_required(login_url="login")
def task_statistics_api(request):
    """
    API trả về dữ liệu thống kê công việc đang được giao
    """
    user = request.user
    
    # Lấy tất cả projects mà user có quyền truy cập
    owned_projects = Project.objects.filter(owner=user)
    member_projects = ProjectMember.objects.filter(user=user).select_related('project')
    
    all_project_ids = set()
    for project in owned_projects:
        all_project_ids.add(project.id)
    for member_project in member_projects:
        all_project_ids.add(member_project.project.id)
    
    # Thống kê theo assignee
    assignee_stats = {}
    for project_id in all_project_ids:
        project = Project.objects.get(id=project_id)
        members = ProjectMember.objects.filter(project=project).select_related('user')
        
        for member in members:
            user_id = member.user.id
            username = member.user.username
            
            if user_id not in assignee_stats:
                assignee_stats[user_id] = {
                    'username': username,
                    'role': member.role,
                    'total_tasks': 0,
                    'todo_tasks': 0,
                    'in_progress_tasks': 0,
                    'done_tasks': 0,
                    'overdue_tasks': 0,
                    'projects': set()
                }
            
            assignee_stats[user_id]['projects'].add(project.name)
            
            user_tasks = Task.objects.filter(assignee=member.user, project=project)
            assignee_stats[user_id]['total_tasks'] += user_tasks.count()
            assignee_stats[user_id]['todo_tasks'] += user_tasks.filter(status='TODO').count()
            assignee_stats[user_id]['in_progress_tasks'] += user_tasks.filter(status='IN_PROGRESS').count()
            assignee_stats[user_id]['done_tasks'] += user_tasks.filter(status='DONE').count()
            
            # Tính overdue tasks
            now = timezone.now()
            overdue_tasks = user_tasks.filter(
                deadline__lt=now,
                status__in=['TODO', 'IN_PROGRESS']
            ).count()
            assignee_stats[user_id]['overdue_tasks'] += overdue_tasks
    
    # Chuyển projects set thành list
    for stats in assignee_stats.values():
        stats['projects'] = list(stats['projects'])
    
    return JsonResponse({
        'success': True,
        'statistics': list(assignee_stats.values())
    })

@login_required(login_url="login")
@require_http_methods(["POST"])
def request_task_completion(request, project_id, task_id):
    """
    Yêu cầu xác nhận hoàn thành công việc
    """
    try:
        project = get_object_or_404(Project, id=project_id)
        user_member = get_user_project_access(request.user, project)
        
        if not user_member:
            return JsonResponse({
                'success': False,
                'error': 'Bạn không có quyền truy cập dự án này'
            }, status=403)
        
        task = get_object_or_404(Task, id=task_id, project=project)
        
        # Chỉ assignee mới có thể yêu cầu hoàn thành
        if task.assignee != request.user:
            return JsonResponse({
                'success': False,
                'error': 'Chỉ người được giao việc mới có thể yêu cầu xác nhận hoàn thành'
            }, status=403)
        
        # Kiểm tra xem đã có request chưa
        existing_request = TaskCompletionRequest.objects.filter(
            task=task,
            requester=request.user,
            status=CompletionRequestStatus.PENDING
        ).first()
        
        if existing_request:
            return JsonResponse({
                'success': False,
                'error': 'Đã có yêu cầu xác nhận hoàn thành đang chờ duyệt'
            }, status=400)
        
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        
        # Tạo completion request
        completion_request = TaskCompletionRequest.objects.create(
            task=task,
            requester=request.user,
            message=message
        )
        
        # Gửi thông báo cho leader/admin/owner
        NotificationService.notify_completion_request(completion_request)
        
        return JsonResponse({
            'success': True,
            'message': 'Yêu cầu xác nhận hoàn thành đã được gửi',
            'request_id': completion_request.id
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
def review_task_completion(request, project_id, request_id):
    """
    Xem xét và phê duyệt/từ chối yêu cầu hoàn thành công việc
    """
    try:
        project = get_object_or_404(Project, id=project_id)
        user_member = get_user_project_access(request.user, project)
        
        if not user_member:
            return JsonResponse({
                'success': False,
                'error': 'Bạn không có quyền truy cập dự án này'
            }, status=403)
        
        # Chỉ OWNER, ADMIN, LEADER mới có thể review
        if user_member.role not in [MemberRole.OWNER, MemberRole.ADMIN, MemberRole.LEADER]:
            return JsonResponse({
                'success': False,
                'error': 'Bạn không có quyền xem xét yêu cầu hoàn thành'
            }, status=403)
        
        completion_request = get_object_or_404(
            TaskCompletionRequest,
            id=request_id,
            task__project=project,
            status=CompletionRequestStatus.PENDING
        )
        
        data = json.loads(request.body)
        action = data.get('action')  # 'approve' hoặc 'reject'
        review_message = data.get('review_message', '').strip()
        
        if action not in ['approve', 'reject']:
            return JsonResponse({
                'success': False,
                'error': 'Hành động không hợp lệ'
            }, status=400)
        
        # Cập nhật completion request
        completion_request.reviewer = request.user
        completion_request.review_message = review_message
        completion_request.reviewed_at = timezone.now()
        
        if action == 'approve':
            completion_request.status = CompletionRequestStatus.APPROVED
            # Cập nhật task status thành DONE
            completion_request.task.status = 'DONE'
            completion_request.task.save()
            message = 'Yêu cầu hoàn thành đã được phê duyệt'
            
            # Gửi thông báo approved
            NotificationService.notify_completion_approved(completion_request, request.user)
        else:
            completion_request.status = CompletionRequestStatus.REJECTED
            message = 'Yêu cầu hoàn thành đã được từ chối'
            
            # Gửi thông báo rejected
            NotificationService.notify_completion_rejected(completion_request, request.user)
        
        completion_request.save()
        
        return JsonResponse({
            'success': True,
            'message': message,
            'action': action
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
def pending_completion_requests_view(request):
    """
    Hiển thị trang danh sách yêu cầu hoàn thành đang chờ duyệt
    """
    return render(request, 'dashboard/pending_completion_requests.html')

@login_required(login_url="login")
def pending_completion_requests_api(request):
    """
    API trả về danh sách yêu cầu hoàn thành đang chờ duyệt
    """
    user = request.user
    
    # Lấy tất cả projects mà user có quyền review (OWNER, ADMIN, LEADER)
    manageable_projects = []
    owned_projects = Project.objects.filter(owner=user)
    manageable_projects.extend(owned_projects)
    
    member_projects = ProjectMember.objects.filter(
        user=user,
        role__in=[MemberRole.ADMIN, MemberRole.LEADER]
    ).select_related('project')
    
    for member_project in member_projects:
        if member_project.project not in manageable_projects:
            manageable_projects.append(member_project.project)
    
    # Lấy pending completion requests
    pending_requests = TaskCompletionRequest.objects.filter(
        task__project__in=manageable_projects,
        status=CompletionRequestStatus.PENDING
    ).select_related('task', 'requester', 'task__project').order_by('-requested_at')
    
    requests_data = []
    for req in pending_requests:
        requests_data.append({
            'id': req.id,
            'task': {
                'id': req.task.id,
                'title': req.task.title,
                'description': req.task.description,
                'priority': req.task.priority,
                'deadline': req.task.deadline.isoformat() if req.task.deadline else None
            },
            'project': {
                'id': req.task.project.id,
                'name': req.task.project.name
            },
            'requester': {
                'id': req.requester.id,
                'username': req.requester.username
            },
            'message': req.message,
            'requested_at': req.requested_at.isoformat()
        })
    
    return JsonResponse({
        'success': True,
        'requests': requests_data
    })

@login_required(login_url="login")
def my_tasks_view(request):
    """
    Hiển thị danh sách tất cả công việc được giao cho user hiện tại
    """
    user = request.user
    
    # Lấy tất cả tasks được giao cho user
    my_tasks = Task.objects.filter(assignee=user).select_related('project').order_by('-created_at')
    
    # Phân loại tasks theo status
    todo_tasks = my_tasks.filter(status='TODO')
    in_progress_tasks = my_tasks.filter(status='IN_PROGRESS')
    done_tasks = my_tasks.filter(status='DONE')
    
    # Tính toán thống kê
    total_tasks = my_tasks.count()
    overdue_tasks = my_tasks.filter(
        deadline__lt=timezone.now(),
        status__in=['TODO', 'IN_PROGRESS']
    ).count()
    
    context = {
        'my_tasks': my_tasks,
        'todo_tasks': todo_tasks,
        'in_progress_tasks': in_progress_tasks,
        'done_tasks': done_tasks,
        'total_tasks': total_tasks,
        'overdue_tasks': overdue_tasks,
        'now': timezone.now()
    }
    
    return render(request, 'dashboard/my_tasks.html', context)

@login_required(login_url="login")
def notifications_view(request):
    """
    Hiển thị trang thông báo
    """
    return render(request, 'dashboard/notifications.html')

@login_required(login_url="login")
def notifications_api(request):
    """
    API trả về danh sách thông báo
    """
    user = request.user
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 20))
    
    offset = (page - 1) * per_page
    notifications = Notification.objects.filter(recipient=user)[offset:offset + per_page]
    
    notifications_data = []
    for notification in notifications:
        notifications_data.append({
            'id': notification.id,
            'type': notification.type,
            'title': notification.title,
            'message': notification.message,
            'is_read': notification.is_read,
            'created_at': notification.created_at.isoformat(),
            'sender': {
                'username': notification.sender.username if notification.sender else None
            } if notification.sender else None,
            'task': {
                'id': notification.task.id,
                'title': notification.task.title
            } if notification.task else None,
            'project': {
                'id': notification.project.id,
                'name': notification.project.name
            } if notification.project else None
        })
    
    # Lấy tổng số thông báo
    total_count = Notification.objects.filter(recipient=user).count()
    unread_count = Notification.objects.filter(recipient=user, is_read=False).count()
    
    return JsonResponse({
        'success': True,
        'notifications': notifications_data,
        'total_count': total_count,
        'unread_count': unread_count,
        'has_more': offset + per_page < total_count
    })

@login_required(login_url="login")
@require_http_methods(["POST"])
def mark_notification_read(request, notification_id):
    """
    Đánh dấu thông báo đã đọc
    """
    success = NotificationService.mark_as_read(notification_id, request.user)
    
    if success:
        return JsonResponse({'success': True, 'message': 'Đã đánh dấu đã đọc'})
    else:
        return JsonResponse({'success': False, 'error': 'Không tìm thấy thông báo'}, status=404)

@login_required(login_url="login")
@require_http_methods(["POST"])
def mark_all_notifications_read(request):
    """
    Đánh dấu tất cả thông báo đã đọc
    """
    count = Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    
    return JsonResponse({
        'success': True, 
        'message': f'Đã đánh dấu {count} thông báo đã đọc'
    })

@login_required(login_url="login")
def unread_notifications_count(request):
    """
    Lấy số lượng thông báo chưa đọc
    """
    count = NotificationService.get_unread_count(request.user)
    return JsonResponse({'unread_count': count})

@login_required(login_url="login")
def check_deadline_warnings_manual(request):
    """
    Kiểm tra deadline warnings thủ công (cho testing)
    """
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    count = NotificationService.check_deadline_warnings()
    return JsonResponse({
        'success': True, 
        'message': f'Đã gửi {count} thông báo deadline warning'
    })
