from django.contrib import admin
from django.urls import path, include
from django.contrib.sitemaps.views import sitemap
from jobs.sitemaps import JobSitemap
from django.views.generic import TemplateView

sitemaps = {
    'jobs': JobSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('jobs.urls')),  # Routes all to jobs app
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
]