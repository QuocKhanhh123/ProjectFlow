from django.core.management.base import BaseCommand
from django.utils import timezone
from dashboard.notification_service import NotificationService


class Command(BaseCommand):
    help = 'Check for tasks approaching deadlines and send notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually sending notifications',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(f'Starting deadline check at {timezone.now()}')
        )

        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No notifications will be sent')
            )

        try:
            if options['dry_run']:
                # In dry run mode, just show what would be done
                from dashboard.models import Task
                from datetime import timedelta
                
                now = timezone.now()
                warning_time_24h = now + timedelta(hours=24)
                warning_time_2h = now + timedelta(hours=2)
                
                tasks_24h = Task.objects.filter(
                    deadline__lte=warning_time_24h,
                    deadline__gt=now,
                    status__in=['TODO', 'IN_PROGRESS'],
                    assignee__isnull=False
                ).count()
                
                tasks_2h = Task.objects.filter(
                    deadline__lte=warning_time_2h,
                    deadline__gt=now,
                    status__in=['TODO', 'IN_PROGRESS'],
                    assignee__isnull=False
                ).count()
                
                self.stdout.write(f'Would send notifications for:')
                self.stdout.write(f'  - {tasks_24h} tasks with 24h deadline warning')
                self.stdout.write(f'  - {tasks_2h} tasks with 2h deadline warning')
            else:
                # Actually send notifications
                notifications_sent = NotificationService.check_deadline_warnings()
                
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully sent {notifications_sent} deadline warning notifications')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error checking deadlines: {str(e)}')
            )
            raise e

        self.stdout.write(
            self.style.SUCCESS(f'Deadline check completed at {timezone.now()}')
        ) 