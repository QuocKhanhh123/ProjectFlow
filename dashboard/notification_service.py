from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from datetime import timedelta
from .models import Notification, NotificationType, Task, Project, TaskCompletionRequest, ProjectMember, MemberRole
from users.models import User


class NotificationService:
    """
    Service để quản lý thông báo và gửi email
    """
    
    @staticmethod
    def create_notification(
        recipient, 
        notification_type, 
        title, 
        message, 
        sender=None, 
        task=None, 
        project=None, 
        completion_request=None,
        send_email=False
    ):
        """
        Tạo thông báo mới
        """
        notification = Notification.objects.create(
            recipient=recipient,
            sender=sender,
            type=notification_type,
            title=title,
            message=message,
            task=task,
            project=project,
            completion_request=completion_request
        )
        
        # Gửi email nếu được yêu cầu
        if send_email:
            NotificationService.send_email_notification(notification)
        
        return notification
    
    @staticmethod
    def send_email_notification(notification):
        """
        Gửi email thông báo
        """
        try:
            subject = f"[ProjectFlow] {notification.title}"
            
            # Render email template
            html_message = render_to_string('emails/notification.html', {
                'notification': notification,
                'recipient_name': notification.recipient.username,
                'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000')
            })
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@projectflow.com'),
                recipient_list=[notification.recipient.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            # Đánh dấu email đã được gửi
            notification.is_email_sent = True
            notification.save(update_fields=['is_email_sent'])
            
            return True
        except Exception as e:
            print(f"Error sending email notification: {e}")
            return False
    
    @staticmethod
    def notify_task_assigned(task, assigned_by):
        """
        Thông báo khi công việc được giao
        """
        if not task.assignee:
            return
        
        title = f"Bạn được giao công việc mới: {task.title}"
        message = f"""
        Bạn đã được giao công việc mới trong dự án "{task.project.name}".
        
        Công việc: {task.title}
        Mô tả: {task.description}
        Độ ưu tiên: {task.get_priority_display()}
        Hạn hoàn thành: {task.deadline.strftime('%d/%m/%Y %H:%M') if task.deadline else 'Không có'}
        Người giao: {assigned_by.username}
        """
        
        return NotificationService.create_notification(
            recipient=task.assignee,
            notification_type=NotificationType.TASK_ASSIGNED,
            title=title,
            message=message.strip(),
            sender=assigned_by,
            task=task,
            project=task.project,
            send_email=True
        )
    
    @staticmethod
    def notify_completion_request(completion_request):
        """
        Thông báo cho leader/admin/owner khi có yêu cầu hoàn thành
        """
        project = completion_request.task.project
        
        # Lấy danh sách người có quyền duyệt
        reviewers = []
        
        # Owner
        reviewers.append(project.owner)
        
        # Admin và Leader
        admin_leader_members = ProjectMember.objects.filter(
            project=project,
            role__in=[MemberRole.ADMIN, MemberRole.LEADER]
        ).select_related('user')
        
        for member in admin_leader_members:
            if member.user not in reviewers:
                reviewers.append(member.user)
        
        title = f"Yêu cầu hoàn thành công việc: {completion_request.task.title}"
        message = f"""
        {completion_request.requester.username} đã yêu cầu xác nhận hoàn thành công việc trong dự án "{project.name}".
        
        Công việc: {completion_request.task.title}
        Mô tả: {completion_request.task.description}
        Tin nhắn từ thành viên: {completion_request.message or 'Không có tin nhắn'}
        Thời gian yêu cầu: {completion_request.requested_at.strftime('%d/%m/%Y %H:%M')}
        """
        
        notifications = []
        for reviewer in reviewers:
            if reviewer != completion_request.requester:  # Không thông báo cho chính người yêu cầu
                notification = NotificationService.create_notification(
                    recipient=reviewer,
                    notification_type=NotificationType.COMPLETION_REQUEST,
                    title=title,
                    message=message.strip(),
                    sender=completion_request.requester,
                    task=completion_request.task,
                    project=project,
                    completion_request=completion_request,
                    send_email=False  # Chỉ thông báo trong app, không gửi email
                )
                notifications.append(notification)
        
        return notifications
    
    @staticmethod
    def notify_deadline_warning(task):
        """
        Thông báo khi sắp hết deadline
        """
        if not task.assignee or not task.deadline:
            return
        
        # Tính thời gian còn lại
        time_left = task.deadline - timezone.now()
        
        if time_left.days > 0:
            time_text = f"{time_left.days} ngày"
        elif time_left.seconds > 3600:
            hours = time_left.seconds // 3600
            time_text = f"{hours} giờ"
        else:
            time_text = "ít hơn 1 giờ"
        
        title = f"⚠️ Công việc sắp hết hạn: {task.title}"
        message = f"""
        Công việc "{task.title}" trong dự án "{task.project.name}" sắp hết hạn.
        
        Thời gian còn lại: {time_text}
        Hạn cuối: {task.deadline.strftime('%d/%m/%Y %H:%M')}
        Độ ưu tiên: {task.get_priority_display()}
        
        Vui lòng hoàn thành công việc hoặc liên hệ với quản lý dự án để gia hạn.
        """
        
        return NotificationService.create_notification(
            recipient=task.assignee,
            notification_type=NotificationType.DEADLINE_WARNING,
            title=title,
            message=message.strip(),
            task=task,
            project=task.project,
            send_email=True
        )
    
    @staticmethod
    def notify_completion_approved(completion_request, reviewer):
        """
        Thông báo khi công việc được chấp nhận hoàn thành
        """
        title = f"✅ Công việc được chấp nhận: {completion_request.task.title}"
        message = f"""
        Yêu cầu hoàn thành công việc của bạn đã được chấp nhận.
        
        Công việc: {completion_request.task.title}
        Dự án: {completion_request.task.project.name}
        Người duyệt: {reviewer.username}
        Tin nhắn từ người duyệt: {completion_request.review_message or 'Không có tin nhắn'}
        Thời gian duyệt: {completion_request.reviewed_at.strftime('%d/%m/%Y %H:%M')}
        
        Chúc mừng bạn đã hoàn thành công việc!
        """
        
        return NotificationService.create_notification(
            recipient=completion_request.requester,
            notification_type=NotificationType.COMPLETION_APPROVED,
            title=title,
            message=message.strip(),
            sender=reviewer,
            task=completion_request.task,
            project=completion_request.task.project,
            completion_request=completion_request,
            send_email=True
        )
    
    @staticmethod
    def notify_completion_rejected(completion_request, reviewer):
        """
        Thông báo khi công việc bị từ chối hoàn thành
        """
        title = f"❌ Yêu cầu hoàn thành bị từ chối: {completion_request.task.title}"
        message = f"""
        Yêu cầu hoàn thành công việc của bạn đã bị từ chối.
        
        Công việc: {completion_request.task.title}
        Dự án: {completion_request.task.project.name}
        Người từ chối: {reviewer.username}
        Lý do: {completion_request.review_message or 'Không có lý do cụ thể'}
        Thời gian từ chối: {completion_request.reviewed_at.strftime('%d/%m/%Y %H:%M')}
        
        Vui lòng kiểm tra lại công việc và gửi yêu cầu mới khi đã hoàn thành.
        """
        
        return NotificationService.create_notification(
            recipient=completion_request.requester,
            notification_type=NotificationType.COMPLETION_REJECTED,
            title=title,
            message=message.strip(),
            sender=reviewer,
            task=completion_request.task,
            project=completion_request.task.project,
            completion_request=completion_request,
            send_email=False  # Không gửi email cho rejection
        )
    
    @staticmethod
    def check_deadline_warnings():
        """
        Kiểm tra và gửi thông báo deadline warning
        Chạy định kỳ (có thể dùng Celery hoặc cron job)
        """
        now = timezone.now()
        
        # Thông báo 24 giờ trước deadline
        warning_time_24h = now + timedelta(hours=24)
        tasks_24h = Task.objects.filter(
            deadline__lte=warning_time_24h,
            deadline__gt=now,
            status__in=['TODO', 'IN_PROGRESS'],
            assignee__isnull=False
        ).exclude(
            notifications__type=NotificationType.DEADLINE_WARNING,
            notifications__created_at__gte=now - timedelta(hours=12)  # Không spam thông báo
        )
        
        # Thông báo 2 giờ trước deadline
        warning_time_2h = now + timedelta(hours=2)
        tasks_2h = Task.objects.filter(
            deadline__lte=warning_time_2h,
            deadline__gt=now,
            status__in=['TODO', 'IN_PROGRESS'],
            assignee__isnull=False
        ).exclude(
            notifications__type=NotificationType.DEADLINE_WARNING,
            notifications__created_at__gte=now - timedelta(hours=1)  # Không spam thông báo
        )
        
        notifications_sent = 0
        
        # Gửi thông báo 24h
        for task in tasks_24h:
            NotificationService.notify_deadline_warning(task)
            notifications_sent += 1
        
        # Gửi thông báo 2h
        for task in tasks_2h:
            NotificationService.notify_deadline_warning(task)
            notifications_sent += 1
        
        return notifications_sent
    
    @staticmethod
    def mark_as_read(notification_id, user):
        """
        Đánh dấu thông báo đã đọc
        """
        try:
            notification = Notification.objects.get(id=notification_id, recipient=user)
            notification.is_read = True
            notification.save(update_fields=['is_read'])
            return True
        except Notification.DoesNotExist:
            return False
    
    @staticmethod
    def get_unread_count(user):
        """
        Lấy số lượng thông báo chưa đọc
        """
        return Notification.objects.filter(recipient=user, is_read=False).count()
    
    @staticmethod
    def get_recent_notifications(user, limit=10):
        """
        Lấy thông báo gần đây
        """
        return Notification.objects.filter(recipient=user)[:limit] 