import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from jobs.models import Job
from jobs.utils import send_job_newsletter
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime
from django.utils import timezone
import xml.etree.ElementTree as ET


class Command(BaseCommand):
    help = "Fetch latest jobs from multiple job sources and notify subscribers"

    def handle(self, *args, **options):
        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=2)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        headers = {'User-Agent': 'Mozilla/5.0'}

        # ✅ Collect newly created jobs for newsletter
        new_jobs = []

        def make_aware(dt):
            """Convert naive datetimes to timezone-aware."""
            if dt is None:
                return timezone.now()
            if timezone.is_naive(dt):
                return timezone.make_aware(dt, timezone=timezone.get_current_timezone())
            return dt

        def safe_create_job(**kwargs):
            """Create job if it doesn't exist; return instance if created."""
            if not Job.objects.filter(title=kwargs['title'], company=kwargs['company']).exists():
                kwargs['date_posted'] = make_aware(kwargs.get('date_posted'))
                job_obj = Job.objects.create(**kwargs)
                new_jobs.append(job_obj)
                return job_obj
            return None

        def fetch_rss(url, source, company_default="Unknown", location="Nigeria"):
            try:
                response = session.get(url, headers=headers, timeout=20)
                response.raise_for_status()
                root = ET.fromstring(response.content)

                for item in root.findall(".//item"):
                    title = item.findtext("title", default="").strip()
                    company = item.findtext("author", default=company_default).strip()
                    description = item.findtext("description", default="")
                    link = item.findtext("link", default="")
                    pub_date = item.findtext("pubDate", default=None)

                    try:
                        date_posted = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z") if pub_date else timezone.now()
                    except Exception:
                        date_posted = timezone.now()

                    safe_create_job(
                        title=title,
                        company=company,
                        location=location,
                        description=description,
                        url=link,
                        source=source,
                        category="",
                        date_posted=date_posted
                    )

                print(f"✅ {source} jobs fetched successfully!")
            except ET.ParseError:
                print(f"⚠️ {source} RSS parse error - skipped.")
            except Exception as e:
                print(f"❌ Error fetching from {source}: {e}")

        # --- REMOTIVE ---
        print("Fetching from Remotive...")
        try:
            response = session.get("https://remotive.com/api/remote-jobs", timeout=20)
            data = response.json()
            for job in data.get("jobs", []):
                pub_date = job.get("publication_date")
                date_posted = datetime.fromisoformat(pub_date.replace('Z', '+00:00')) if pub_date else timezone.now()
                safe_create_job(
                    title=job.get("title"),
                    company=job.get("company_name"),
                    location=job.get("candidate_required_location", "Remote"),
                    description=job.get("description", ""),
                    url=job.get("url"),
                    source="Remotive",
                    category=job.get("category", ""),
                    date_posted=date_posted
                )
            print("✅ Remotive jobs fetched successfully!")
        except Exception as e:
            print(f"❌ Remotive error: {e}")

        # --- ADZUNA ---
        print("Fetching from Adzuna...")
        try:
            url = (
                f"https://api.adzuna.com/v1/api/jobs/gb/search/1?"
                f"app_id={settings.ADZUNA_APP_ID}&app_key={settings.ADZUNA_APP_KEY}"
                f"&results_per_page=50&what=remote&where=Nigeria"
            )
            response = session.get(url, timeout=20)
            data = response.json()
            for job in data.get("results", []):
                created = job.get("created")
                date_posted = datetime.strptime(created, "%Y-%m-%dT%H:%M:%SZ") if created else timezone.now()
                safe_create_job(
                    title=job.get("title"),
                    company=job.get("company", {}).get("display_name", "Unknown"),
                    location=job.get("location", {}).get("display_name", "Nigeria"),
                    description=job.get("description", ""),
                    url=job.get("redirect_url"),
                    source="Adzuna",
                    category=job.get("category", {}).get("label", ""),
                    date_posted=date_posted
                )
            print("✅ Adzuna jobs fetched successfully!")
        except Exception as e:
            print(f"❌ Adzuna error: {e}")

        # --- RSS Sources ---
        fetch_rss("https://reliefweb.int/jobs/rss.xml?country=175", "ReliefWeb")
        fetch_rss("http://www.hotnigerianjobs.com/feed/rss.xml", "HotNigerianJobs")
        fetch_rss("https://ngojobsinafrica.com/job-location/nigeria/feed/", "NGOJobsInAfrica")
        fetch_rss("https://www.jobzilla.ng/feed/", "Jobzilla")
        fetch_rss("https://www.careerjet.com.ng/rss/", "Careerjet")
        fetch_rss("https://unjobs.org/themes/development.rss", "UN Jobs")
        fetch_rss("https://www.devex.com/jobs/search.rss", "Devex")

        print("🎯 All job sources processed successfully!")

        # --- ✅ SEND NEWSLETTER TO SUBSCRIBERS ---
        if new_jobs:
            print(f"📬 Sending newsletter for {len(new_jobs)} new jobs...")
            send_job_newsletter(new_jobs)
            print("✅ Newsletter sent successfully!")
        else:
            print("ℹ️ No new jobs, skipping newsletter.")
