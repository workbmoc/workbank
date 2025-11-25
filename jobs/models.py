# jobs/models.py

from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.contrib.auth.models import User


class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    date_subscribed = models.DateTimeField(auto_now_add=True)
    paystack_reference = models.CharField(max_length=100, blank=True, null=True, unique=True)

    def __str__(self):
        return self.email


class Job(models.Model):
    title = models.CharField(max_length=300)
    company = models.CharField(max_length=200, blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    source = models.CharField(max_length=100, blank=True, null=True)
    category = models.CharField(max_length=200, blank=True, null=True)
    date_posted = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)
    employer_email = models.EmailField(blank=True, null=True)
    
    # 🔑 ADDED: Paystack reference for payment verification
    paystack_reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True,
        help_text="Paystack transaction reference (e.g., 123_job)"
    )

    def __str__(self):
        return f"{self.title} at {self.company or 'Unknown'}"

    def get_absolute_url(self):
        return reverse('job_detail', kwargs={'job_id': self.id})

# jobs/models.py

class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=255, unique=False, blank=True)  # ← unique=False for now
    
    author = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Leave blank to auto-assign"
    )
    # existing fields...
    summary = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=200, blank=True, null=True)

    
    excerpt = models.CharField(
        max_length=300,
        blank=True,
        null=True,
        help_text="Short summary for lists & SEO. Auto-filled from content if empty."
    )
    
    content = models.TextField()
    
    featured_image = models.ImageField(
        upload_to='blog/',
        blank=True,
        null=True
    )
    
    meta_description = models.CharField(
        max_length=160,
        blank=True,
        null=True,
        help_text="SEO meta description (max 160 chars)"
    )
    
    meta_keywords = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Comma-separated keywords for SEO"
    )
    
    SOURCE_CHOICES = [
        ('internal', 'WorkBank Team'),
        ('external', 'External Source'),
        ('guest', 'Guest Author'),
    ]
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default='internal'
    )
    
    date_posted = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        # Auto-generate slug
        if not self.slug:
            self.slug = slugify(self.title)[:50]
            base_slug = self.slug
            counter = 1
            while BlogPost.objects.filter(slug=self.slug).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        
        # Auto-generate excerpt
        if not self.excerpt and self.content:
            # Trim to ~280 chars, break at word
            if len(self.content) > 280:
                self.excerpt = self.content[:280].rsplit(' ', 1)[0] + '...'
            else:
                self.excerpt = self.content
        
        # Auto-assign author if missing
        if not self.author:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            self.author = User.objects.first()  # picks first user (e.g., superuser)
        
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog_detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-date_posted']
        verbose_name = 'Blog Post'
        verbose_name_plural = 'Blog Posts'