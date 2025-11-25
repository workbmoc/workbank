# jobs/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.core.mail import send_mail, BadHeaderError
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import Http404

from paystackapi.transaction import Transaction

from .models import Job, Subscriber, BlogPost
from .forms import JobSubmissionForm, SubscriberForm

# Initialize Paystack (already in settings)
paystack_secret_key = settings.PAYSTACK_SECRET_KEY


# Newsletter subscription (supports AJAX + fallback; handles GET now)
def subscribe_newsletter(request):
    if request.method == "POST":
        # Handle AJAX
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            email = request.POST.get("email", "").strip()
            if not email or "@" not in email:
                return JsonResponse({"status": "error", "message": "❌ Please enter a valid email."}, status=400)

            subscriber, created = Subscriber.objects.get_or_create(email=email)
            if created:
                return JsonResponse({"status": "success", "message": "✅ Subscribed! Thanks for joining."})
            else:
                return JsonResponse({"status": "info", "message": "ℹ️ You’re already subscribed."})

        # Fallback for non-JS POST
        else:
            form = SubscriberForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "✅ Subscribed! Thanks for joining.")
            else:
                messages.warning(request, "⚠️ Invalid or duplicate email.")
            return redirect(request.META.get("HTTP_REFERER", "/"))
    else:
        # Handle GET: Redirect to home or show message (avoids 405)
        messages.info(request, "Please use the subscription form to join.")
        return redirect("/")


# ✅ Homepage (job list with search filters) — extends base.html
def home(request):
    queryset = Job.objects.all().order_by("-is_paid", "-date_posted")

    keyword = request.GET.get("keyword", "").strip()
    location = request.GET.get("location", "").strip()
    category = request.GET.get("category", "").strip()

    if keyword:
        queryset = queryset.filter(Q(title__icontains=keyword) | Q(description__icontains=keyword))
    if location:
        queryset = queryset.filter(location__icontains=location)
    if category:
        queryset = queryset.filter(category__icontains=category)

    paginator = Paginator(queryset, 10)
    page_number = request.GET.get("page")
    jobs = paginator.get_page(page_number)

    return render(request, "jobs/home.html", {
        "jobs": jobs,
        "active_page": "home"
    })


# ✅ Full Job List Page — extends base.html
def job_list(request):
    queryset = Job.objects.all().order_by("-date_posted")

    keyword = request.GET.get("keyword", "").strip()
    location = request.GET.get("location", "").strip()
    category = request.GET.get("category", "").strip()

    if keyword:
        queryset = queryset.filter(Q(title__icontains=keyword) | Q(description__icontains=keyword))
    if location:
        queryset = queryset.filter(location__icontains=location)
    if category:
        queryset = queryset.filter(category__icontains=category)

    paginator = Paginator(queryset, 10)
    page_number = request.GET.get("page")
    jobs = paginator.get_page(page_number)

    return render(request, "jobs/job_list.html", {
        "jobs": jobs,
        "active_page": "jobs"
    })


# ✅ Blog List
def blog_list(request):
    blogs = BlogPost.objects.filter(is_published=True).order_by("-date_posted")
    paginator = Paginator(blogs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "jobs/blogs.html", {
        "blogs": page_obj,
        "active_page": "blogs"
    })


# ✅ Blog Detail (by slug) — MAIN ENTRY POINT
def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    return render(request, 'jobs/blog_detail.html', {
        'post': post,
        'active_page': 'blogs'
    })


# ✅ Redirect from /blog/<id>/ to slug-based URL (SEO-safe, avoids 404)
def blog_detail_by_id(request, id):
    post = get_object_or_404(BlogPost, id=id, is_published=True)
    return redirect('blog_detail', slug=post.slug, permanent=True)


# ✅ Static Pages
def about(request):
    return render(request, "jobs/about.html", {"active_page": "about"})

def privacy(request):
    return render(request, "jobs/privacy.html", {"active_page": "privacy"})

def terms(request):
    return render(request, "jobs/terms.html", {"active_page": "terms"})

def partners(request):
    return render(request, 'jobs/partners.html', {'active_page': 'partners'})

def disclaimer(request):
    return render(request, "jobs/disclaimer.html", {"active_page": "disclaimer"})

def jobseekers(request):
    return render(request, "jobs/jobseekers.html", {"active_page": "jobseekers"})

def categories(request):
    return render(request, "jobs/categories.html", {"active_page": "categories"})

def locations(request):
    return render(request, "jobs/locations.html", {"active_page": "locations"})

def contact(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        message = request.POST.get("message", "").strip()

        if not (name and email and message):
            messages.error(request, "⚠️ Please fill out all fields.")
        else:
            subject = f"New Contact Message from {name}"
            body = f"From: {name}\nEmail: {email}\n\nMessage:\n{message}"
            try:
                send_mail(
                    subject,
                    body,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.EMAIL_HOST_USER]
                )
                messages.success(request, "✅ Your message has been sent successfully!")
                return redirect("contact")
            except BadHeaderError:
                messages.error(request, "❌ Invalid header found.")
            except Exception as e:
                messages.error(request, f"❌ Failed to send: {str(e)}")

    return render(request, "jobs/contact.html", {"active_page": "contact"})


# ✅ Job Submission + Paystack Init
# ✅ FIXED submit_job — ensure paystack_reference is saved BEFORE Paystack call
# ✅ FINAL submit_job — guaranteed paystack_reference save
def submit_job(request):
    if request.method == "POST":
        form = JobSubmissionForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.is_paid = False  # explicit
            job.save()  # ← First save → now job.id exists

            # ✅ IMMEDIATELY generate and save reference
            reference = f"{job.id}_job"
            job.paystack_reference = reference
            job.save(update_fields=['paystack_reference'])  # ✅ Only this field → fast & safe

            # 🔍 DEBUG: verify it's saved
            # from django.db import connection
            # print("DEBUG: Saved reference =", Job.objects.get(id=job.id).paystack_reference)

            amount = 500000  # ₦5,000 in kobo
            email = form.cleaned_data["employer_email"]

            try:
                response = Transaction.initialize(
                    reference=reference,
                    amount=amount,
                    email=email,
                    callback_url=request.build_absolute_uri("/payment-callback/")
                )
            except Exception as e:
                # ❌ Paystack error — but job & reference are already saved
                messages.error(request, f"❌ Payment gateway error: {e}. Job saved (unpaid).")
                return render(request, "jobs/submit_job.html", {"form": form})

            if response and response.get("status"):
                return redirect(response["data"]["authorization_url"])
            else:
                error_msg = response.get("message", "Unknown error")
                messages.error(request, f"❌ Payment setup failed: {error_msg}")
    else:
        form = JobSubmissionForm()

    return render(request, "jobs/submit_job.html", {"form": form})
# ✅ Paystack Payment Callback (secure, idempotent)
def payment_callback(request):
    reference = request.GET.get("reference")
    if not reference:
        return HttpResponse("<h3 class='text-danger'>❌ Missing reference.</h3>", status=400)

    try:
        response = Transaction.verify(reference=reference)
    except Exception as e:
        return HttpResponse(f"<h3 class='text-danger'>❌ Verification error: {e}</h3>", status=500)

    if not (response.get("status") and response["data"].get("status") == "success"):
        return HttpResponse("<h3 class='text-danger'>❌ Payment failed or incomplete.</h3>", status=400)

    # Secure lookup: match reference stored in Job
    try:
        job = Job.objects.get(paystack_reference=reference)
    except Job.DoesNotExist:
        return HttpResponse("<h3 class='text-warning'>⚠️ Invalid or already processed reference.</h3>", status=400)

    # Avoid double-processing
    if job.is_paid:
        return HttpResponse("<h3 class='text-info'>ℹ️ Payment already processed.</h3>", status=200)

    # Final validation (optional: check amount, email)
    amount_paid = response["data"]["amount"]
    expected_amount = 500000
    if amount_paid != expected_amount:
        return HttpResponse(
            f"<h3 class='text-danger'>❌ Suspicious amount: ₦{amount_paid/100:.2f} (expected ₦{expected_amount/100:.2f})</h3>",
            status=400
        )

    # Mark as paid
    job.is_paid = True
    job.save()

    return HttpResponse("<h3 class='text-success'>✅ Payment successful! Your job is now featured.</h3>", status=200)


# ✅ Job Detail
def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    return render(request, "jobs/job_detail.html", {
        "job": job,
        "active_page": "home"  # or "jobs", depending on UX
    })