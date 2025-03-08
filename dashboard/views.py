# dashboard/views.py

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Q
from django.contrib.auth.models import User
from django.core.paginator import Paginator

from projects.models import Project, Category
from projects.forms import ProjectDashboardForm
from users.forms import UserDashboardForm, ProfileDashboardForm
from users.models import Profile


@staff_member_required
def dashboard_view(request):
    total_users = User.objects.count()
    total_projects = Project.objects.count()
    # Show more categories if needed
    top_categories = Category.objects.annotate(num_projects=Count('project')).order_by('-num_projects')[:5]
    context = {
        'total_users': total_users,
        'total_projects': total_projects,
        'top_categories': top_categories,
    }
    return render(request, 'dashboard/dashboard.html', context)


@staff_member_required
def manage_users_view(request):
    search_query = request.GET.get('search', '')
    users_qs = User.objects.all()
    if search_query:
        users_qs = users_qs.filter(username__icontains=search_query)
    users_qs = users_qs.order_by('-date_joined')
    paginator = Paginator(users_qs, 10)  # 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj, 'search_query': search_query}
    return render(request, 'dashboard/manage_users.html', context)


@staff_member_required
def manage_projects_view(request):
    search_query = request.GET.get('search', '')
    projects_qs = Project.objects.all()
    if search_query:
        projects_qs = projects_qs.filter(title__icontains=search_query)
    projects_qs = projects_qs.order_by('-created_at')
    paginator = Paginator(projects_qs, 10)  # 10 per page
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
    """ Custom edit page for a User and their Profile. """
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
    """ Custom edit page for a Project. """
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
