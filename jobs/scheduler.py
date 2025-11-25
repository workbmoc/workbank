import schedule
import time
import os
import sys
import django

# Add your project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Go one directory up (to reach project root)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set the correct Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workbank.settings')  # 👈 CHANGE this to your real project name

django.setup()

from django.core.management import call_command

def run_fetch_jobs():
    print("⏰ Running scheduled job: fetch_jobs")
    call_command('fetch_jobs')

# Run every 24 hours
schedule.every(24).hours.do(run_fetch_jobs)

print("✅ Scheduler started — will run every 24 hours.")
while True:
    schedule.run_pending()
    time.sleep(60)

