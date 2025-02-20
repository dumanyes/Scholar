# views.py
from django.contrib import messages

from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.generic import ListView, DetailView

from .forms import ProjectForm
from .models import Project, ProjectApplication, Notification, User, ChatMessage, ChatRoom
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Exists, OuterRef


class MarketplaceView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'marketplace/marketplace.html'
    context_object_name = 'projects'
    paginate_by = 10

    def get_queryset(self):
        queryset = Project.objects.filter(is_active=True).order_by('-created_at')
        # Add annotation to check if user has applied
        if self.request.user.is_authenticated:
            queryset = queryset.annotate(
                has_applied=Exists(
                    ProjectApplication.objects.filter(
                        project=OuterRef('pk'),
                        applicant=self.request.user
                    )
                )
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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

# views.py
class MyProjectsView(LoginRequiredMixin, ListView):
    template_name = 'marketplace/my_projects.html'
    context_object_name = 'projects'

    def get_queryset(self):
        return Project.objects.filter(owner=self.request.user)


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'marketplace/project_form.html'

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    fields = ['title', 'description', 'category', 'skills_required', 'is_active']
    template_name = 'marketplace/project_form.html'
    context_object_name = 'project'

    def get_queryset(self):
        return Project.objects.filter(owner=self.request.user)

    def get_success_url(self):
        return reverse_lazy('my-projects')


class ProjectToggleView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        project = get_object_or_404(
            Project,
            pk=self.kwargs['pk'],
            owner=self.request.user
        )
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
        # Create notification
        Notification.objects.create(
            user=application.applicant,
            message=f"Your application to {application.project.title} has been {status.lower()}",
            link=reverse('project-detail', kwargs={'pk': application.project.pk})
        )

    return redirect('project-detail', pk=application.project.pk)


@login_required
def chat_view(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    current_user = request.user

    # Get or create chat room
    room = ChatRoom.objects.filter(participants=current_user).filter(participants=other_user).distinct().first()

    if not room:
        room = ChatRoom.objects.create()
        room.participants.add(current_user, other_user)

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            ChatMessage.objects.create(
                room=room,
                sender=current_user,
                content=content
            )
            return redirect('chat', user_id=user_id)

    messages = room.messages.all().order_by('timestamp')

    context = {
        'room': room,
        'other_user': other_user,
        'messages': messages,
    }
    return render(request, 'chat/chat.html', context)