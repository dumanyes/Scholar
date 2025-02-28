
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DetailView, UpdateView, DeleteView
from django.contrib import messages


from django.urls import reverse
from django.views.generic import CreateView

from .forms import ProjectForm, ProjectApplicationForm
from .models import Notification, SkillsCategory, Skill, Language, RequiredRole

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Exists, OuterRef, Q
from django.views.generic import ListView
from .models import Project, ProjectApplication, Category


from django.db.models import Q, Exists, OuterRef
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from .models import Project, ProjectApplication, Category
from django.db.models import Q, OuterRef, Subquery, CharField


class MarketplaceView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'marketplace/marketplace.html'
    context_object_name = 'projects'
    paginate_by = 10

    def get_queryset(self):
        queryset = Project.objects.filter(is_active=True)

        # Category filtering
        categories_param = self.request.GET.get('categories', '')
        if categories_param:
            cat_ids = [cid.strip() for cid in categories_param.split(',') if cid.strip()]
            if cat_ids:
                queryset = queryset.filter(category__id__in=cat_ids).distinct()

        # Skill filtering (exact match for selected skills)
        skills_param = self.request.GET.get('skills', '')
        if skills_param:
            skill_ids = [s.strip() for s in skills_param.split(',') if s.strip()]
            if skill_ids:
                for skill_id in skill_ids:
                    queryset = queryset.filter(skills_required__id=skill_id)
                queryset = queryset.distinct()

        # Text search
        q = self.request.GET.get('q', '')
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q) |
                Q(project_mission__icontains=q) |
                Q(project_objectives__icontains=q)
            )

        # Annotate application status for current user using Subquery
        app_qs = ProjectApplication.objects.filter(
            project=OuterRef('pk'),
            applicant=self.request.user
        ).values('status')[:1]
        queryset = queryset.annotate(
            application_status=Subquery(app_qs, output_field=CharField())
        )

        # Sorting
        time_sort = self.request.GET.get('time_sort', '')
        match_sort = self.request.GET.get('match_sort', '')

        if time_sort:
            if time_sort == 'recent':
                return queryset.order_by('-created_at')
            if time_sort == 'old':
                return queryset.order_by('created_at')

        if match_sort in ['mostmatcher', 'mostunmatched']:
            projects = list(queryset)
            reverse_sort = (match_sort == 'mostmatcher')
            projects.sort(key=lambda p: p.get_skill_match(self.request.user), reverse=reverse_sort)
            return projects

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'all_categories': Category.objects.all(),
            'user_skills': set(s.name.lower() for s in self.request.user.profile.skills.all()),
            'selected_categories': self.request.GET.get('categories', '').split(','),
            'selected_skills': self.request.GET.get('skills', '').split(','),
            'current_query': self.request.GET.get('q', ''),
            'time_sort': self.request.GET.get('time_sort', ''),
            'match_sort': self.request.GET.get('match_sort', '')
        })
        return context




class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'marketplace/project_detail.html'
    context_object_name = 'project'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Increment the view count
        self.object.view_count += 1
        self.object.save(update_fields=['view_count'])
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sort_app = self.request.GET.get('sort_applications')
        applications = list(self.object.applications.all())
        if sort_app == 'most_matched':
            applications.sort(key=lambda a: a.matching_score, reverse=True)
        elif sort_app == 'most_unmatched':
            applications.sort(key=lambda a: a.matching_score)
        elif sort_app == 'most_recent':
            applications.sort(key=lambda a: a.applied_at, reverse=True)
        elif sort_app == 'most_old':
            applications.sort(key=lambda a: a.applied_at)
        context['sorted_applications'] = applications
        if self.request.user.is_authenticated:
            context['user_application'] = self.object.applications.filter(applicant=self.request.user).first()
        return context


class ApplyProjectView(View):
    def get(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        # If an application already exists, you might want to redirect or inform the user.
        if ProjectApplication.objects.filter(project=project, applicant=request.user).exists():
            messages.info(request, "You have already applied to this project.")
            return redirect('project-detail', pk=project.id)
        form = ProjectApplicationForm()
        context = {
            'project': project,
            'form': form,
        }
        return render(request, 'marketplace/apply_project.html', context)

    def post(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        if ProjectApplication.objects.filter(project=project, applicant=request.user).exists():
            messages.info(request, "You have already applied to this project.")
            return redirect('project-detail', pk=project.id)
        form = ProjectApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.project = project
            application.applicant = request.user
            application.status = 'PENDING'
            application.save()
            # Update the application's count on the project.
            project.application_count = project.applications.count()
            project.save(update_fields=['application_count'])
            messages.success(request, 'Your application has been submitted successfully!')
            return redirect('project-detail', pk=project.id)
        else:
            context = {
                'project': project,
                'form': form,
            }
            return render(request, 'marketplace/apply_project.html', context)



class DeleteApplicationView(LoginRequiredMixin, DeleteView):
    model = ProjectApplication
    template_name = 'marketplace/application_confirm_delete.html'  # A confirmation page
    success_url = reverse_lazy('my-requests')  # Or wherever you want to redirect the applicant

    def get_queryset(self):
        # Only allow deletion of applications that belong to the current user.
        return ProjectApplication.objects.filter(applicant=self.request.user)

@login_required
def withdraw_application(request, project_id):
    application = ProjectApplication.objects.filter(project__id=project_id, applicant=request.user).first()
    if application:
        if application.status == 'PENDING':
            application.delete()
            messages.success(request, "Your application has been withdrawn.")
        else:
            messages.error(request, "You can only withdraw a pending application.")
    else:
        messages.error(request, "You have not applied to this project.")
    return redirect('marketplace')



class MyProjectsView(LoginRequiredMixin, ListView):
    template_name = 'marketplace/my_projects.html'
    context_object_name = 'projects'

    def get_queryset(self):
        return Project.objects.filter(owner=self.request.user)



from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView
from .forms import ProjectForm
from .models import Project, Skill, Category, SkillsCategory, Language, RequiredRole


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'marketplace/project_create.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['skill_categories'] = SkillsCategory.objects.prefetch_related('subcategories__skills').all()
        context['available_categories'] = Category.objects.all()
        context['languages'] = Language.objects.all()
        context['required_roles'] = RequiredRole.objects.all()
        return context

    def form_valid(self, form):
        """ Custom validation and debugging for project creation. """
        print("🟢 Form is valid. Attempting to create project.")

        # Get the list of selected skill IDs from cleaned_data.
        skill_ids = form.cleaned_data.get('skills_required', [])
        selected_skills = Skill.objects.filter(id__in=skill_ids)

        if len(selected_skills) < 1:
            messages.error(self.request, "Please select at least 1 skills.")
            print("❌ ERROR: Less than 1 skills selected.")
            return self.render_to_response(self.get_context_data(form=form))

        # Save the project instance.
        form.instance.owner = self.request.user
        self.object = form.save(commit=False)
        self.object.save()
        form.save_m2m()
        self.object.skills_required.set(selected_skills)

        # Debugging categories
        categories_str = self.request.POST.get('categories', '')
        print(f"📌 Categories received: {categories_str}")
        if categories_str:
            category_ids = [cid.strip() for cid in categories_str.split(',') if cid.strip()]
            categories_qs = Category.objects.filter(id__in=category_ids)
            self.object.category.set(categories_qs)

        # Debugging languages
        languages_str = self.request.POST.get('languages', '')
        print(f"📌 Languages received: {languages_str}")
        if languages_str:
            language_ids = [lid.strip() for lid in languages_str.split(',') if lid.strip()]
            language_objs = Language.objects.filter(id__in=language_ids)
            self.object.languages.set(language_objs)

        # Debugging required roles
        roles_str = self.request.POST.get('required_roles', '')
        print(f"📌 Required Roles received: {roles_str}")
        if roles_str:
            role_ids = [rid.strip() for rid in roles_str.split(',') if rid.strip()]
            role_objs = RequiredRole.objects.filter(id__in=role_ids)
            self.object.required_roles.set(role_objs)

        messages.success(self.request, "✅ Project created successfully!")
        return redirect(self.object.get_absolute_url())

    def form_invalid(self, form):
        """ Debugging for form invalid cases. """
        print("❌ ERROR: Form is invalid.")
        print("🔴 Form Errors:", form.errors.as_json())
        messages.error(self.request, "Something went wrong. Please check your inputs.")
        return self.render_to_response(self.get_context_data(form=form))


import json
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView
from .forms import ProjectForm
from .models import Project, Skill, Category, SkillsCategory, Language, RequiredRole

class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'marketplace/project_update.html'
    context_object_name = 'project'

    def get_queryset(self):
        # Only allow the owner to update the project.
        return Project.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['skill_categories'] = SkillsCategory.objects.prefetch_related(
            'subcategories__skills'
        ).all()
        context['available_categories'] = Category.objects.all()
        context['min_selections'] = 1
        context['languages'] = Language.objects.all()
        context['required_roles'] = RequiredRole.objects.all()
        # Prepopulate many-to-many selections both as lists and comma-separated strings
        context['selected_categories_list'] = [str(cat.id) for cat in self.object.category.all()]
        context['selected_skills_list'] = [str(skill.id) for skill in self.object.skills_required.all()]
        context['selected_languages_list'] = [str(lang.id) for lang in self.object.languages.all()]
        context['selected_required_roles_list'] = [str(role.id) for role in self.object.required_roles.all()]

        context['selected_categories'] = ",".join(context['selected_categories_list'])
        context['selected_skills'] = ",".join(context['selected_skills_list'])
        context['selected_languages'] = ",".join(context['selected_languages_list'])
        context['selected_required_roles'] = ",".join(context['selected_required_roles_list'])
        return context

    def form_valid(self, form):
        # Get the list of selected skill IDs from cleaned_data.
        skill_ids = form.cleaned_data.get('skills_required', [])
        selected_skills = Skill.objects.filter(id__in=skill_ids)
        if len(selected_skills) < 1:
            messages.error(self.request, 'Please select at least 1 skills.')
            context = self.get_context_data()
            return self.render_to_response(context)

        # Update the project instance.
        form.instance.owner = self.request.user
        self.object = form.save(commit=False)
        self.object.save()
        form.save_m2m()
        self.object.skills_required.set(selected_skills)

        # Process categories from the hidden input (IDs)
        categories_str = self.request.POST.get('categories', '')
        if categories_str:
            category_ids = [cid.strip() for cid in categories_str.split(',') if cid.strip()]
            categories_qs = Category.objects.filter(id__in=category_ids)
            self.object.category.set(categories_qs)

        # Process languages field (hidden input as a comma-separated list of IDs)
        languages_str = self.request.POST.get('languages', '')
        if languages_str:
            language_ids = [lid.strip() for lid in languages_str.split(',') if lid.strip()]
            language_objs = Language.objects.filter(id__in=language_ids)
            self.object.languages.set(language_objs)

        # Process required roles field (hidden input as a comma-separated list of IDs)
        roles_str = self.request.POST.get('required_roles', '')
        if roles_str:
            role_ids = [rid.strip() for rid in roles_str.split(',') if rid.strip()]
            role_objs = RequiredRole.objects.filter(id__in=role_ids)
            self.object.required_roles.set(role_objs)

        messages.success(self.request, "Project updated successfully!")
        return redirect(self.object.get_absolute_url())



class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Project
    template_name = 'marketplace/project_confirm_delete.html'  # Confirmation page
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
    # Retrieve the user by username
    profile_user = get_object_or_404(User, username=username)

    # Retrieve all projects owned by the user
    user_projects = Project.objects.filter(owner=profile_user)

    # Prepare the context for the template
    context = {
        'profile_user': profile_user,
        'projects_count': user_projects.count(),
        'projects': user_projects,  # Include projects if you want to display them
    }

    # Render the profile template with the given context
    return render(request, 'marketplace/project_profile.html', context)


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
@login_required
def chat_view(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    current_user = request.user

    # Find or create a room with exactly these two participants
    rooms = ChatRoom.objects.filter(participants=current_user).filter(participants=other_user)
    room = None
    for r in rooms:
        if r.participants.count() == 2:
            room = r
            break
    if not room:
        room = ChatRoom.objects.create()
        room.participants.add(current_user, other_user)



    # Retrieve all messages in chronological order
    chat_messages = room.messages.all().order_by('timestamp')
    context = {
        'room': room,
        'other_user': other_user,
        'chat_messages': chat_messages,  # <-- use 'chat_messages' key
        'room_id': room.id,
    }
    return render(request, 'chat/chat.html', context)


@login_required
def chat_messages(request, user_id):
    """
    Returns a JSON response with all messages for polling.
    This endpoint is used by the chat template's fetch call.
    It ensures that only the room with exactly the two participants is used.
    """
    other_user = get_object_or_404(User, id=user_id)
    current_user = request.user

    # Find a room that includes both users and has exactly these two participants.
    rooms = ChatRoom.objects.filter(participants=current_user).filter(participants=other_user)
    room = None
    for r in rooms:
        if r.participants.count() == 2:
            room = r
            break

    if not room:
        return JsonResponse({'new_messages': []})

    messages_qs = room.messages.all().order_by('timestamp')
    messages_list = []
    for message in messages_qs:
        avatar_url = ""
        if hasattr(message.sender, 'profile') and message.sender.profile.avatar:
            avatar_url = message.sender.profile.avatar.url
        messages_list.append({
            'sender': message.sender.username,
            'sender_avatar': avatar_url,
            'content': message.content,
            'timestamp': message.timestamp.strftime("%H:%M"),
            'read': message.read,
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
