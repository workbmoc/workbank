from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from jobs.models import Job
from jobs.utils import send_job_newsletter

class Command(BaseCommand):
    help = "Send daily newsletter to subscribers with new jobs from the past 24 hours"

    def handle(self, *args, **options):
        now = timezone.now()
        since = now - timedelta(hours=24)
        new_jobs = Job.objects.filter(date_posted__gte=since).order_by('-date_posted')

        if new_jobs.exists():
            self.stdout.write(f"📨 Sending newsletter for {new_jobs.count()} new jobs...")
            send_job_newsletter(new_jobs)
            self.stdout.write(self.style.SUCCESS("✅ Newsletter sent successfully!"))
        else:
            self.stdout.write("ℹ️ No new jobs found in the last 24 hours.")
