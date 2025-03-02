from django.shortcuts import render

# Create your views here.
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Count
from django.contrib.auth.models import User
from projects.models import Project, Category


@staff_member_required  # Restrict access to staff members
def dashboard_view(request):
    total_users = User.objects.count()
    total_projects = Project.objects.filter(is_active=True).count()
    top_categories = Category.objects.annotate(num_projects=Count('project')).order_by('-num_projects')[:5]

    context = {
        'total_users': total_users,
        'total_projects': total_projects,
        'top_categories': top_categories,
    }
    return render(request, 'dashboard/dashboard.html', context)

