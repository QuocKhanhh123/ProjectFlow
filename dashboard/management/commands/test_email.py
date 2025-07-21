from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import traceback


class Command(BaseCommand):
    help = 'Test email configuration by sending a test email'

    def add_arguments(self, parser):
        parser.add_argument(
            '--to',
            type=str,
            default='trandinhminhquan207@gmail.com',
            help='Email address to send test email to'
        )

    def handle(self, *args, **options):
        recipient_email = options['to']
        
        self.stdout.write(
            self.style.SUCCESS(f'Testing email configuration...')
        )
        self.stdout.write(f'EMAIL_BACKEND: {settings.EMAIL_BACKEND}')
        self.stdout.write(f'EMAIL_HOST: {settings.EMAIL_HOST}')
        self.stdout.write(f'EMAIL_PORT: {settings.EMAIL_PORT}')
        self.stdout.write(f'EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}')
        self.stdout.write(f'EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}')
        self.stdout.write(f'DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}')
        self.stdout.write(f'Sending to: {recipient_email}')
        self.stdout.write('-' * 50)
        
        try:
            subject = 'ProjectFlow - Test Email Configuration'
            message = f"""
Xin chào!

Đây là email test từ hệ thống ProjectFlow để kiểm tra cấu hình email.

Thông tin:
- Thời gian gửi: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}
- Hệ thống: ProjectFlow
- Backend: {settings.EMAIL_BACKEND}

Nếu bạn nhận được email này, cấu hình email đã hoạt động thành công! 🎉

Trân trọng,
ProjectFlow System
            """.strip()
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                fail_silently=False,
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Email sent successfully to {recipient_email}!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to send email: {str(e)}')
            )
            self.stdout.write('Full traceback:')
            self.stdout.write(traceback.format_exc()) 