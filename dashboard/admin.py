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
    list_display = ('title', 'project', 'assignee', 'status', 'priority', 'deadline', 'created_at')
    search_fields = ('title', 'description', 'assignee__username')
    list_filter = ('status', 'priority', 'created_at', 'deadline')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('title', 'description', 'project', 'assignee')
        }),
        ('Trạng thái & Ưu tiên', {
            'fields': ('status', 'priority', 'deadline')
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

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

@admin.register(ProjectInvitation)
class ProjectInvitationAdmin(admin.ModelAdmin):
    list_display = ('receiver_email', 'project', 'role', 'sender', 'status', 'sent_at', 'expires_at')
    list_filter = ('role', 'status', 'sent_at')
    search_fields = ('receiver_email', 'project__name', 'sender__username')
    readonly_fields = ('sent_at',)
    fieldsets = (
        ('Thông tin lời mời', {
            'fields': ('receiver_email', 'project', 'role', 'sender')
        }),
        ('Trạng thái', {
            'fields': ('status', 'expires_at')
        }),
        ('Thời gian', {
            'fields': ('sent_at',),
            'classes': ('collapse',)
        }),
    )

@admin.register(TaskCompletionRequest)
class TaskCompletionRequestAdmin(admin.ModelAdmin):
    list_display = ('task', 'requester', 'status', 'requested_at', 'reviewer', 'reviewed_at')
    list_filter = ('status', 'requested_at', 'reviewed_at')
    search_fields = ('task__title', 'requester__username', 'reviewer__username')
    readonly_fields = ('requested_at', 'reviewed_at')
    fieldsets = (
        ('Yêu cầu hoàn thành', {
            'fields': ('task', 'requester', 'message')
        }),
        ('Phản hồi', {
            'fields': ('status', 'reviewer', 'review_message')
        }),
        ('Thời gian', {
            'fields': ('requested_at', 'reviewed_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'recipient', 'type', 'is_read', 'is_email_sent', 'created_at')
    list_filter = ('type', 'is_read', 'is_email_sent', 'created_at')
    search_fields = ('title', 'message', 'recipient__username', 'sender__username')
    readonly_fields = ('created_at',)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active', 'last_active', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    readonly_fields = ('date_joined', 'last_login', 'created_at', 'updated_at', 'last_active')
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('username', 'email', 'first_name', 'last_name')
        }),
        ('Quyền hạn', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Thời gian hoạt động', {
            'fields': ('last_login', 'last_active', 'date_joined', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )