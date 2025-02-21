# views.py
import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Exists, OuterRef
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProjectForm
from .models import Project, ProjectApplication, Notification, User, ChatMessage, ChatRoom, Category

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Exists, OuterRef, Q
from django.views.generic import ListView
from .models import Project, ProjectApplication, Category


class MarketplaceView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'marketplace/marketplace.html'
    context_object_name = 'projects'
    paginate_by = 10  # Note: When sorting in Python, pagination might not work as expected.

    def get_queryset(self):
        # Start with active projects
        queryset = Project.objects.filter(is_active=True)

        # --- Filtering ---
        # Filter by category (accept multiple IDs, comma separated)
        categories_param = self.request.GET.get('categories', '')
        if categories_param:
            cat_ids = [cid.strip() for cid in categories_param.split(',') if cid.strip()]
            if cat_ids:
                queryset = queryset.filter(category__id__in=cat_ids).distinct()

        # Filter by skills (text-based, comma-separated)
        skills_param = self.request.GET.get('skills', '')
        if skills_param:
            skill_list = [s.strip() for s in skills_param.split(',') if s.strip()]
            for skill in skill_list:
                queryset = queryset.filter(skills_required__icontains=skill)

        # Text search: title or description
        q = self.request.GET.get('q', '')
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) | Q(description__icontains=q)
            )

        # Annotate if user has applied
        if self.request.user.is_authenticated:
            queryset = queryset.annotate(
                has_applied=Exists(
                    ProjectApplication.objects.filter(
                        project=OuterRef('pk'),
                        applicant=self.request.user
                    )
                )
            )

        # --- Sorting ---
        # Get new sort parameters from GET
        time_sort = self.request.GET.get('time_sort', '')
        match_sort = self.request.GET.get('match_sort', '')

        # If time sort is provided, apply it.
        if time_sort:
            if time_sort == 'recent':
                queryset = queryset.order_by('-created_at')
            elif time_sort == 'old':
                queryset = queryset.order_by('created_at')
            return queryset

        # Otherwise, if match sort is provided, sort in Python.
        if match_sort in ['mostmatcher', 'mostunmatched']:
            projects = list(queryset)
            reverse = (match_sort == 'mostmatcher')
            projects.sort(key=lambda p: p.get_skill_match(self.request.user), reverse=reverse)
            return projects

        # Default: order by most recent.
        queryset = queryset.order_by('-created_at')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Provide all categories for clickable filtering in the template.
        context['all_categories'] = Category.objects.all()
        # Also provide the user's skills (lowercased) for highlighting.
        context['user_skills'] = set(s.name.lower() for s in self.request.user.profile.skills.all())
        return context




class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'marketplace/project_detail.html'
    context_object_name = 'project'


class ApplyProjectView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        project = get_object_or_404(Project, id=self.kwargs['project_id'])
        application, created = ProjectApplication.objects.get_or_create(
            project=project,
            applicant=request.user,
            defaults={'status': 'PENDING'}
        )

        if created:
            messages.success(request, 'Application submitted successfully!')
        else:
            messages.warning(request, 'You have already applied to this project')

        return redirect('project-detail', pk=project.id)


class MyProjectsView(LoginRequiredMixin, ListView):
    template_name = 'marketplace/my_projects.html'
    context_object_name = 'projects'

    def get_queryset(self):
        return Project.objects.filter(owner=self.request.user)


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'marketplace/project_create.html'  # Separate template for creation

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        available_skills = list(self.request.user.profile.skills.values_list('name', flat=True))
        available_categories = list(Category.objects.values_list('name', flat=True))
        context['available_skills_json'] = json.dumps(available_skills)
        context['available_categories_json'] = json.dumps(available_categories)
        # Pass language and role options for checkboxes
        context['language_options'] = json.dumps(["English", "Русский", "Қазақша"])
        context['role_options'] = json.dumps(["ML Engineer", "Backend Developer", "Frontend Developer", "Project Manager"])
        return context

    def form_valid(self, form):
        # Assign the project owner.
        form.instance.owner = self.request.user
        # Save the instance (without m2m fields) so it gets an ID.
        self.object = form.save(commit=False)
        self.object.save()
        form.save_m2m()  # Save many-to-many fields coming from the form

        # Handle additional many-to-many assignment for categories via a hidden input.
        categories_str = self.request.POST.get('categories', '')
        if categories_str:
            category_names = [name.strip() for name in categories_str.split(',') if name.strip()]
            for cat_name in category_names:
                category_obj, created = Category.objects.get_or_create(name=cat_name)
                self.object.category.add(category_obj)

        messages.success(self.request, "Project created successfully!")
        return redirect(self.object.get_absolute_url())



class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'marketplace/project_update.html'  # Separate template for update
    context_object_name = 'project'

    def get_queryset(self):
        # Only allow the owner to update the project.
        return Project.objects.filter(owner=self.request.user)

    def get_success_url(self):
        messages.success(self.request, "Project updated successfully!")
        return reverse_lazy('project-detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass available skills and categories as JSON strings for use in autocomplete.
        available_skills = list(self.request.user.profile.skills.values_list('name', flat=True))
        available_categories = list(Category.objects.values_list('name', flat=True))
        context['available_skills_json'] = json.dumps(available_skills)
        context['available_categories_json'] = json.dumps(available_categories)
        # Pass existing categories to prepopulate the category tags.
        context['existing_categories'] = [cat.name for cat in self.object.category.all()]
        return context



class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Project
    template_name = 'marketplace/project_confirm_delete.html'  # Separate template for delete confirmation
    success_url = reverse_lazy('my-projects')

    def get_queryset(self):
        # Only allow deletion of projects owned by the current user.
        return Project.objects.filter(owner=self.request.user)


class ProjectToggleView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        project = get_object_or_404(Project, pk=self.kwargs['pk'], owner=request.user)
        project.is_active = not project.is_active
        project.save()
        return redirect('my-projects')


def user_profile(request, username):
    user = get_object_or_404(User, username=username)
    context = {
        'profile_user': user,
        'projects_count': Project.objects.filter(owner=user).count(),
    }
    return render(request, 'users/profile.html', context)


@login_required
def update_application(request, pk, status):
    application = get_object_or_404(ProjectApplication, pk=pk, project__owner=request.user)
    previous_status = application.status
    application.status = status
    application.save()

    if previous_status != status:
        # Create a notification for the applicant.
        Notification.objects.create(
            user=application.applicant,
            message=f"Your application to {application.project.title} has been {status.lower()}",
            link=reverse('project-detail', kwargs={'pk': application.project.pk})
        )

    return redirect('project-detail', pk=application.project.pk)




import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from .models import User, ChatRoom, ChatMessage

@login_required
def chat_view(request, user_id):
    # Get the other user to chat with.
    other_user = get_object_or_404(User, id=user_id)
    current_user = request.user

    # Get or create a chat room for the two users.
    room = ChatRoom.objects.filter(participants=current_user).filter(participants=other_user).first()
    if not room:
        room = ChatRoom.objects.create()
        room.participants.add(current_user, other_user)

    # Handle new message submission.
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            ChatMessage.objects.create(
                room=room,
                sender=current_user,
                content=content
            )
        return redirect('chat', user_id=user_id)

    # Retrieve all messages in chronological order.
    messages_qs = room.messages.all().order_by('timestamp')
    context = {
        'room': room,
        'other_user': other_user,
        'messages': messages_qs,
    }
    return render(request, 'chat/chat.html', context)

@login_required
def chat_messages(request, user_id):
    """
    Returns a JSON response with all messages for polling.
    This endpoint is used by the chat template's fetch call.
    """
    other_user = get_object_or_404(User, id=user_id)
    current_user = request.user

    room = ChatRoom.objects.filter(participants=current_user).filter(participants=other_user).first()
    if not room:
        return JsonResponse({'new_messages': []})

    messages_qs = room.messages.all().order_by('timestamp')
    messages_list = []
    for message in messages_qs:
        messages_list.append({
            'sender': message.sender.username,
            'content': message.content,
            'timestamp': message.timestamp.strftime("%H:%M"),
            'read': message.read,  # use 'read' because that's the field name in ChatMessage model
        })
    return JsonResponse({'new_messages': messages_list})

class MyRequestsView(LoginRequiredMixin, ListView):
    model = ProjectApplication
    template_name = 'marketplace/my_requests.html'
    context_object_name = 'applications'
    paginate_by = 10

    def get_queryset(self):
        # Returns all project applications sent by the current user, newest first.
        return ProjectApplication.objects.filter(applicant=self.request.user).order_by('-applied_at')
