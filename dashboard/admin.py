from django.contrib import admin
from .models import Project, Task, Comment, ProjectMember, ProjectInvitation, TaskCompletionRequest, Notification
from users.models import User
# Register your models here.
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'status', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('status', 'created_at')
    ordering = ('-created_at',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'status',)
    search_fields = ('title', 'description')
    list_filter = ('status',)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'created_at')
    search_fields = ('content',)
    list_filter = ('created_at',)
    ordering = ('-created_at',)

@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'role', 'joined_at')
    list_filter = ('role', 'joined_at')
    search_fields = ('user__username', 'project__name')

@admin.register(TaskCompletionRequest)
class TaskCompletionRequestAdmin(admin.ModelAdmin):
    list_display = ('task', 'requester', 'status', 'requested_at', 'reviewer')
    list_filter = ('status', 'requested_at')
    search_fields = ('task__title', 'requester__username', 'reviewer__username')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'recipient', 'type', 'is_read', 'is_email_sent', 'created_at')
    list_filter = ('type', 'is_read', 'is_email_sent', 'created_at')
    search_fields = ('title', 'message', 'recipient__username', 'sender__username')
    readonly_fields = ('created_at',)