from django.core.mail import send_mail
from django.conf import settings
from .models import Subscriber
from django.template.loader import render_to_string

def send_job_newsletter(new_jobs):
    """
    Send a newsletter to all subscribers when new jobs are added.
    `new_jobs` is a list of Job objects.
    """
    subscribers = Subscriber.objects.all()
    if not subscribers.exists() or not new_jobs:
        return

    subject = "🔥 New Jobs Alert from WorkBank"
    # Prepare plain text message
    job_list = "\n\n".join([f"{job.title} at {job.company}\nLocation: {job.location}\nLink: {job.url}" for job in new_jobs])
    message = f"Hello!\n\nHere are the latest job postings:\n\n{job_list}\n\nVisit our site for more jobs!"

    recipient_list = [s.email for s in subscribers]

    # You can also create an HTML template for better formatting
    html_message = render_to_string('jobs/newsletter_template.html', {'jobs': new_jobs})

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            fail_silently=False,
            html_message=html_message
        )
    except Exception as e:
        print(f"❌ Failed to send newsletter: {e}")

# utils.py
from .models import BlogPost
from django.utils.text import slugify

def generate_blog_posts():
    topics = [
        "How to Write a Winning Resume",
        "Top 10 Remote Jobs in 2025",
        "Preparing for a Job Interview",
        "Latest Trends in the Job Market",
        "How to Stay Productive While Working from Home",
        "Tech Skills Employers Want in 2025",
    ]

    for topic in topics:
        if not BlogPost.objects.filter(title=topic).exists():
            excerpt = f"{topic} — Learn key tips and insights to boost your career in today’s world."
            content = f"""
            <p><strong>{topic}</strong> is one of the most discussed career subjects in 2025.</p>
            <p>In this article, we’ll explore strategies, real-world advice, and current trends to help you succeed.</p>
            <p>Stay tuned for more updates on job hunting, resume building, and interview skills.</p>
            """
            BlogPost.objects.create(
                title=topic,
                excerpt=excerpt,
                content=content,
                source="Auto Generator"
            )
