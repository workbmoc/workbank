import feedparser
import time
import requests
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.files.base import ContentFile
from django.utils.text import Truncator
from jobs.models import BlogPost

# 🔹 Optional summarizer (safe for Windows)
try:
    import torch
    from transformers import pipeline

    summarizer = pipeline(
        "summarization",
        model="facebook/bart-large-cnn",
        device=-1,
        framework="pt"
    )
    SUMMARIZER_AVAILABLE = True
    print("✅ Summarizer ready (CPU mode)")
except Exception as e:
    print(f"⚠️ Summarizer disabled: {e}")
    SUMMARIZER_AVAILABLE = False


def auto_summary(text):
    """Generate summary safely, fallback to truncation."""
    if len(text) < 100:
        return text
    if not SUMMARIZER_AVAILABLE:
        return Truncator(text).words(25)
    try:
        result = summarizer(
            text[:1024],
            max_length=100,
            min_length=30,
            do_sample=False
        )
        return result[0]["summary_text"]
    except Exception as e:
        print(f"Summarization failed: {e}")
        return Truncator(text).words(25)


def download_image_to_post(post, image_url):
    """Download remote image into BlogPost.featured_image"""
    if not image_url:
        return
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; WorkBankBot/1.0)'}
        response = requests.get(image_url, timeout=10, headers=headers)
        if response.status_code == 200:
            ext = '.jpg' if 'jpg' in image_url.lower() else '.png'
            filename = f"blog_{post.id}_{int(time.time())}{ext}"
            post.featured_image.save(filename, ContentFile(response.content), save=True)
            print(f"✅ Saved image: {filename}")
    except Exception as e:
        print(f"⚠️ Image download failed for {image_url}: {e}")


# 🔹 RSS sources
SOURCES = [
    {'name': 'TechCrunch - Jobs', 'url': 'https://techcrunch.com/category/jobs/feed/', 'category': 'Tech Jobs'},
    {'name': 'The Guardian - Careers', 'url': 'https://www.theguardian.com/careers/rss', 'category': 'Career Advice'},
    {'name': 'Glassdoor Blog', 'url': 'https://www.glassdoor.com/blog/feed/', 'category': 'Job Market'},
    {'name': 'Nairaland - Jobs', 'url': 'https://www.nairaland.com/jobs/feed', 'category': 'Nigeria Jobs'},
    {'name': 'Remote OK - Jobs', 'url': 'https://remoteok.com/feeds/remote-jobs.rss', 'category': 'Remote Jobs'},
]


class Command(BaseCommand):
    help = 'Fetch job & career news from RSS feeds and save as BlogPosts'

    def handle(self, *args, **options):
        created_count = 0

        for source in SOURCES:
            self.stdout.write(f"\n📡 Fetching from: {source['name']}")
            try:
                feed = feedparser.parse(source['url'])
                self.stdout.write(f"✅ Got {len(feed.entries)} entries")

                for entry in feed.entries[:5]:  # limit to 5 latest per source
                    title = entry.get('title', '').strip()[:200]
                    if not title or BlogPost.objects.filter(title=title, source=source['name']).exists():
                        self.stdout.write(f"  ⚠ Skipped existing post: {title[:50]}...")
                        continue

                    content = entry.get('content', [{}])[0].get('value', '') or entry.get('summary', '')
                    summary = auto_summary(content)

                    url = entry.get('link', '').strip()  # optional, store if you add field

                    post = BlogPost(
                        title=title or url,
                        summary=summary,
                        content=content,
                        source=source['name'],
                        category=source['category'],
                        date_posted=timezone.now(),
                    )

                    # Image detection
                    image_url = None
                    if hasattr(entry, 'media_content') and entry.media_content:
                        image_url = entry.media_content[0].get('url')
                    elif entry.get('media_thumbnail'):
                        image_url = entry.media_thumbnail[0]['url']
                    elif entry.get('links'):
                        for link in entry.links:
                            if link.get('type', '').startswith('image/'):
                                image_url = link.href
                                break
                    elif entry.get('enclosures'):
                        image_url = entry.enclosures[0].get('href')

                    post.featured_image_url = image_url if image_url else None  # store temporarily if needed
                    post.save()
                    created_count += 1
                    self.stdout.write(f"  ➕ Created: {title[:50]}...")

                    if image_url:
                        download_image_to_post(post, image_url)

                    time.sleep(1)  # prevent overloading servers

            except Exception as e:
                self.stderr.write(f"❌ Error fetching {source['name']}: {e}")

        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 Successfully fetched {created_count} blog posts!')
        )
