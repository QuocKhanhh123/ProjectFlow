from django.db import models
from django.utils import timezone
from users.models import User

class ProjectStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    COMPLETED = 'COMPLETED', 'Completed'
    ON_HOLD = 'ON_HOLD', 'On Hold'

class MemberRole(models.TextChoices):
    OWNER = 'OWNER', 'Owner'
    ADMIN = 'ADMIN', 'Admin'
    LEADER = 'LEADER', 'Leader'
    MEMBER = 'MEMBER', 'Member'

class InvitationStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    ACCEPTED = 'ACCEPTED', 'Accepted'
    DECLINED = 'DECLINED', 'Declined'
    EXPIRED = 'EXPIRED', 'Expired'

class TaskStatus(models.TextChoices):
    TODO = 'TODO', 'Todo'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    DONE = 'DONE', 'Done'

class TaskPriority(models.TextChoices):
    LOW = 'LOW', 'Low'
    MEDIUM = 'MEDIUM', 'Medium'
    HIGH = 'HIGH', 'High'

class CompletionRequestStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    APPROVED = 'APPROVED', 'Approved'
    REJECTED = 'REJECTED', 'Rejected'

class NotificationType(models.TextChoices):
    TASK_ASSIGNED = 'TASK_ASSIGNED', 'Task Assigned'
    COMPLETION_REQUEST = 'COMPLETION_REQUEST', 'Completion Request'
    DEADLINE_WARNING = 'DEADLINE_WARNING', 'Deadline Warning'
    COMPLETION_APPROVED = 'COMPLETION_APPROVED', 'Completion Approved'
    COMPLETION_REJECTED = 'COMPLETION_REJECTED', 'Completion Rejected'

class Project(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=ProjectStatus.choices,
        default=ProjectStatus.ACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_projects'
    )

    class Meta:
        db_table = 'projects'

class ProjectMember(models.Model):
    id = models.AutoField(primary_key=True)
    role = models.CharField(
        max_length=20,
        choices=MemberRole.choices,
        default=MemberRole.MEMBER
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='projects'
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='members'
    )

    class Meta:
        db_table = 'project_members'
        unique_together = ['user', 'project']

class ProjectInvitation(models.Model):
    id = models.AutoField(primary_key=True)
    role = models.CharField(
        max_length=20,
        choices=MemberRole.choices,
        default=MemberRole.MEMBER
    )
    status = models.CharField(
        max_length=20,
        choices=InvitationStatus.choices,
        default=InvitationStatus.PENDING
    )
    sent_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_invitations'
    )
    receiver_email = models.EmailField()
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='invitations'
    )

    class Meta:
        db_table = 'project_invitations'
        unique_together = ['receiver_email', 'project']

class Task(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.TODO
    )
    priority = models.CharField(
        max_length=20,
        choices=TaskPriority.choices,
        default=TaskPriority.MEDIUM
    )
    deadline = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    assignee = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='tasks'
    )

    class Meta:
        db_table = 'tasks'

class TaskCompletionRequest(models.Model):
    id = models.AutoField(primary_key=True)
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='completion_requests'
    )
    requester = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='completion_requests'
    )
    status = models.CharField(
        max_length=20,
        choices=CompletionRequestStatus.choices,
        default=CompletionRequestStatus.PENDING
    )
    message = models.TextField(blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewer = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_completion_requests'
    )
    review_message = models.TextField(blank=True)

    class Meta:
        db_table = 'task_completion_requests'
        unique_together = ['task', 'requester']

class Comment(models.Model):
    id = models.AutoField(primary_key=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
    )

    class Meta:
        db_table = 'comments'

class Notification(models.Model):
    id = models.AutoField(primary_key=True)
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    sender = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='sent_notifications'
    )
    type = models.CharField(
        max_length=30,
        choices=NotificationType.choices
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    is_email_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Related objects for context
    task = models.ForeignKey(
        Task,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    project = models.ForeignKey(
        Project,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    completion_request = models.ForeignKey(
        TaskCompletionRequest,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.recipient.username}"
