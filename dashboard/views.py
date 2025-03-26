# dashboard/views.py

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Q
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta
import json

from dashboard.models import ContactMessage
from projects.models import Project, Category, ChatMessage, Notification, ProjectApplication
from projects.forms import ProjectDashboardForm
from users.forms import UserDashboardForm, ProfileDashboardForm
from users.models import Profile


@staff_member_required
def dashboard_view(request):
    time_filter = request.GET.get('time_filter', 'all_time')

    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = None
    end_date = None

    if time_filter == 'today':
        start_date = today
        end_date = timezone.now()
    elif time_filter == 'yesterday':
        start_date = today - timedelta(days=1)
        end_date = today
    elif time_filter == 'last_week':
        start_date = today - timedelta(days=7)
        end_date = timezone.now()
    elif time_filter == 'last_month':
        start_date = today - timedelta(days=30)
        end_date = timezone.now()
    elif time_filter == 'last_year':
        start_date = today - timedelta(days=365)
        end_date = timezone.now()
    else:
        pass  # "all_time"

    # Metrics (Users, Projects, etc.)
    if start_date and end_date:
        total_users = User.objects.filter(date_joined__range=(start_date, end_date)).count()
        total_projects = Project.objects.filter(created_at__range=(start_date, end_date)).count()
        pending_applications_count = ProjectApplication.objects.filter(
            status='PENDING', applied_at__range=(start_date, end_date)
        ).count()
        total_contact_messages = ContactMessage.objects.filter(submitted_at__range=(start_date, end_date)).count()
        active_projects_count = Project.objects.filter(is_active=True, created_at__range=(start_date, end_date)).count()
        inactive_projects_count = Project.objects.filter(is_active=False, created_at__range=(start_date, end_date)).count()
        total_chat_messages = ChatMessage.objects.filter(timestamp__range=(start_date, end_date)).count()
        total_notifications = Notification.objects.filter(created_at__range=(start_date, end_date)).count()
    else:
        total_users = User.objects.count()
        total_projects = Project.objects.count()
        pending_applications_count = ProjectApplication.objects.filter(status='PENDING').count()
        total_contact_messages = ContactMessage.objects.count()
        active_projects_count = Project.objects.filter(is_active=True).count()
        inactive_projects_count = Project.objects.filter(is_active=False).count()
        total_chat_messages = ChatMessage.objects.count()
        total_notifications = Notification.objects.count()

    # Top Categories
    if start_date and end_date:
        project_ids = Project.objects.filter(created_at__range=(start_date, end_date)).values_list('id', flat=True)
        top_categories = (
            Project.objects.filter(id__in=project_ids)
            .values('category__name')
            .annotate(num_projects=Count('category'))
            .order_by('-num_projects')[:5]
        )
    else:
        top_categories = (
            Project.objects.values('category__name')
            .annotate(num_projects=Count('category'))
            .order_by('-num_projects')[:5]
        )

    # Monthly Registrations
    monthly_registrations = (
        User.objects.annotate(month=TruncMonth('date_joined'))
            .values('month')
            .annotate(total=Count('id'))
            .order_by('month')
    )
    monthly_registration_labels = []
    monthly_registration_data = []
    for item in monthly_registrations:
        if item['month']:
            month_str = item['month'].strftime('%b %Y')
        else:
            month_str = 'Unknown'
        monthly_registration_labels.append(month_str)
        monthly_registration_data.append(item['total'])

    # Monthly Project Submissions
    monthly_projects = (
        Project.objects.annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(total=Count('id'))
            .order_by('month')
    )
    monthly_project_labels = []
    monthly_project_data = []
    for item in monthly_projects:
        if item['month']:
            month_str = item['month'].strftime('%b %Y')
        else:
            month_str = 'Unknown'
        monthly_project_labels.append(month_str)
        monthly_project_data.append(item['total'])

    # Popular Projects (by view_count)
    popular_projects = Project.objects.order_by('-view_count')[:5]

    context = {
        'time_filter': time_filter,
        'total_users': total_users,
        'total_projects': total_projects,
        'pending_applications_count': pending_applications_count,
        'total_contact_messages': total_contact_messages,
        'active_projects_count': active_projects_count,
        'inactive_projects_count': inactive_projects_count,
        'total_chat_messages': total_chat_messages,
        'total_notifications': total_notifications,
        'top_categories': top_categories,

        # The line charts need these:
        'monthly_registration_labels': json.dumps(monthly_registration_labels),
        'monthly_registration_data': json.dumps(monthly_registration_data),
        'monthly_project_labels': json.dumps(monthly_project_labels),
        'monthly_project_data': json.dumps(monthly_project_data),

        'popular_projects': popular_projects,
    }
    return render(request, 'dashboard/dashboard.html', context)


@staff_member_required
def manage_users_view(request):
    search_query = request.GET.get('search', '')
    users_qs = User.objects.all()
    if search_query:
        users_qs = users_qs.filter(username__icontains=search_query)
    users_qs = users_qs.order_by('-date_joined')

    paginator = Paginator(users_qs, 30)  # Show 30 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_verified': User.objects.filter(profile__is_verified=True).count(),
        'total_unverified': User.objects.filter(profile__is_verified=False).count(),
        'total_staff': User.objects.filter(is_staff=True).count(),
    }
    return render(request, 'dashboard/manage_users.html', context)


@staff_member_required
def manage_projects_view(request):
    search_query = request.GET.get('search', '')
    projects_qs = Project.objects.all()
    if search_query:
        projects_qs = projects_qs.filter(title__icontains=search_query)
    projects_qs = projects_qs.order_by('-created_at')
    paginator = Paginator(projects_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj, 'search_query': search_query}
    return render(request, 'dashboard/manage_projects.html', context)


@staff_member_required
def bulk_user_action_view(request):
    if request.method == "POST":
        action = request.POST.get("action")
        ids = request.POST.getlist("user_ids")
        if action == "delete" and ids:
            User.objects.filter(id__in=ids).delete()
    return redirect("dashboard-users")


@staff_member_required
def edit_user_view(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    profile_obj = user_obj.profile
    if request.method == "POST":
        user_form = UserDashboardForm(request.POST, instance=user_obj)
        profile_form = ProfileDashboardForm(request.POST, instance=profile_obj)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect("dashboard-users")
    else:
        user_form = UserDashboardForm(instance=user_obj)
        profile_form = ProfileDashboardForm(instance=profile_obj)
    context = {
        "user_obj": user_obj,
        "user_form": user_form,
        "profile_form": profile_form,
    }
    return render(request, "dashboard/edit_user.html", context)


@staff_member_required
def edit_project_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if request.method == "POST":
        form = ProjectDashboardForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect("dashboard-projects")
    else:
        form = ProjectDashboardForm(instance=project)
    context = {
        "project": project,
        "form": form,
    }
    return render(request, "dashboard/edit_project.html", context)


@staff_member_required
def delete_project_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    project.delete()
    return redirect("dashboard-projects")


@staff_member_required
def contact_messages_view(request):
    qs = ContactMessage.objects.all().order_by('-submitted_at')

    subject_filter = request.GET.get('subject', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    # Filter by subject if selected (exact match; adjust to icontains if needed)
    if subject_filter:
        qs = qs.filter(subject=subject_filter)

    if start_date:
        qs = qs.filter(submitted_at__gte=start_date)
    if end_date:
        qs = qs.filter(submitted_at__lte=end_date)

    paginator = Paginator(qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get a list of distinct subjects for filtering
    subjects = ContactMessage.objects.values_list('subject', flat=True).distinct()

    context = {
        'page_obj': page_obj,
        'subject_filter': subject_filter,
        'start_date': start_date,
        'end_date': end_date,
        'subjects': subjects,
    }
    return render(request, 'dashboard/contact_messages.html', context)


@staff_member_required
def manage_applications_view(request):
    applications = ProjectApplication.objects.all().order_by('-applied_at')
    return render(request, 'dashboard/manage_applications.html', {'applications': applications})


@staff_member_required
def contact_message_detail(request, pk):
    msg = get_object_or_404(ContactMessage, pk=pk)
    return render(request, 'dashboard/contact_message_detail.html', {'msg': msg})


@staff_member_required
def contact_message_delete(request, pk):
    msg = get_object_or_404(ContactMessage, pk=pk)
    if request.method == "POST":
        msg.delete()
        return redirect('dashboard-contacts')
    return render(request, 'dashboard/contact_message_confirm_delete.html', {'msg': msg})

@staff_member_required
def edit_user_view(request, user_id):
    """Allows staff to edit a user's main account fields and Profile fields."""
    user_obj = get_object_or_404(User, id=user_id)
    profile_obj = user_obj.profile

    if request.method == "POST":
        user_form = UserDashboardForm(request.POST, instance=user_obj)
        profile_form = ProfileDashboardForm(request.POST, request.FILES, instance=profile_obj)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect("dashboard-users")  # or wherever you want to go after saving
    else:
        user_form = UserDashboardForm(instance=user_obj)
        profile_form = ProfileDashboardForm(instance=profile_obj)

    context = {
        "user_obj": user_obj,
        "user_form": user_form,
        "profile_form": profile_form,
    }
    return render(request, "dashboard/dash_edit_user.html", context)