from django.urls import path
from . import views

urlpatterns = [
    # Core pages
    path('', views.home, name='home'),
    path('jobs/', views.job_list, name='job_list'),
    path('job/<int:job_id>/', views.job_detail, name='job_detail'),

    # Blogs
    path('blogs/', views.blog_list, name='blogs'),  # Blog list page
    path('blogs/', views.blog_list, name='blogs'),  # NOT blog_list
    path('blogs/<int:id>/', views.blog_detail_by_id, name='blog_detail_by_id'),  # Redirect old ID URLs
    path('blogs/<slug:slug>/', views.blog_detail, name='blog_detail'),  # Slug-based detail page

    # Static/core informational pages
    path('about/', views.about, name='about'),
    path('partners/', views.partners, name='partners'),
    path('contact/', views.contact, name='contact'),
    path('privacy/', views.privacy, name='privacy'),
    path('terms/', views.terms, name='terms'),
    path('disclaimer/', views.disclaimer, name='disclaimer'),
    path('jobseekers/', views.jobseekers, name='jobseekers'),
    path('categories/', views.categories, name='categories'),
    path('locations/', views.locations, name='locations'),

    # Functional endpoints
    path('submit-job/', views.submit_job, name='submit_job'),
    path('payment-callback/', views.payment_callback, name='payment_callback'),
    path('subscribe/', views.subscribe_newsletter, name='subscribe_newsletter'),
]
