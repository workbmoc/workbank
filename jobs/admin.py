from django.contrib import admin
from .models import Job, Subscriber, BlogPost
from django.utils.html import format_html
from .models import BlogPost

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'location', 'is_paid', 'date_posted', 'created_at')
    search_fields = ('title', 'company', 'location', 'description')
    list_filter = ('is_paid', 'date_posted', 'created_at')

@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'date_subscribed')
    search_fields = ('email',)

# ✅ jobs/admin.py

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'author',
        'date_posted',
        'is_published',
        'slug_display',  # custom column
    )
    list_filter = (
        'is_published',
        'date_posted',
        'author',
        # 'category',  # add later if you add categories
    )
    search_fields = ('title', 'excerpt', 'content', 'author__username')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'date_posted'
    ordering = ('-date_posted',)
    
    # Optional: Show slug truncated in list
    @admin.display(description="Slug")
    def slug_display(self, obj):
        return format_html('<code>{}</code>', obj.slug[:30] + ("..." if len(obj.slug) > 30 else ""))