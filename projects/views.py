from urllib import request

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, UpdateView, DeleteView, CreateView, ListView
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.db.models import Q, OuterRef, Subquery, CharField, Case, When, Count, Exists
import json

from .forms import ProjectForm, ProjectApplicationForm
from .models import (
    Notification, SkillsCategory, Skill, Language, RequiredRole,
    ChatFolder, ChatRoom, FavoriteProject, Project, ProjectApplication,
    Category, ChatMessage
)
from django.contrib.auth.mixins import LoginRequiredMixin
from users.models import Profile
from projects.recommendation import rank_projects_with_faiss, recommend_projects_for_user  # Updated import



from django.db.models import Q, OuterRef, Subquery, CharField, Case, When
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from projects.models import Project, ProjectApplication, Category, ChatMessage, ChatRoom
from projects.recommendation import rank_projects_with_faiss, recommend_projects_for_user

from django.db.models import Q, OuterRef, Subquery, CharField, Case, When
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from projects.models import Project, ProjectApplication, Category, ChatMessage, ChatRoom
from projects.recommendation import rank_projects_with_faiss, recommend_projects_for_user

class MarketplaceView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'marketplace/marketplace.html'
    context_object_name = 'projects'

    def get_queryset(self):
        queryset = Project.objects.filter(is_active=True)

        # Category filtering
        categories_param = self.request.GET.get('categories', '')
        if categories_param:
            cat_ids = [cid.strip() for cid in categories_param.split(',') if cid.strip()]
            if cat_ids:
                queryset = queryset.filter(category__id__in=cat_ids).distinct()

        # Skill filtering
        skills_param = self.request.GET.get('skills', '')
        if skills_param:
            skill_ids = [s.strip() for s in skills_param.split(',') if s.strip()]
            if skill_ids:
                for skill_id in skill_ids:
                    queryset = queryset.filter(skills_required__id=skill_id)
                queryset = queryset.distinct()

        # Text search filtering
        q = self.request.GET.get('q', '')
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q) |
                Q(project_mission__icontains=q) |
                Q(project_objectives__icontains=q)
            )

        # Annotate application status for the current user using a Subquery
        app_qs = ProjectApplication.objects.filter(
            project=OuterRef('pk'),
            applicant=self.request.user
        ).values('status')[:1]
        queryset = queryset.annotate(
            application_status=Subquery(app_qs, output_field=CharField())
        )

        # Allow overriding ordering by time if requested
        time_sort = self.request.GET.get('time_sort', '')
        if time_sort == 'recent':
            return queryset.order_by('-created_at')
        if time_sort == 'old':
            return queryset.order_by('created_at')

        # Otherwise, reorder projects based on FAISS recommendations.
        projects_list = list(queryset)
        if not projects_list:
            return queryset.order_by('-created_at')

        recommended_order, faiss_scores = rank_projects_with_faiss(projects_list, self.request.user)
        # Save the mapping for potential use in context.
        self.faiss_scores = faiss_scores
        ordering = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(recommended_order)])
        qs = queryset.filter(pk__in=recommended_order).order_by(ordering)
        # Convert to list and attach the FAISS score to each project.
        projects_with_score = list(qs)
        for project in projects_with_score:
            project.faiss_score = self.faiss_scores.get(project.id, 0)
        return projects_with_score

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Unread notifications
        unread_notifications = self.request.user.notifications.filter(read=False).order_by('-created_at')
        notifications_count = unread_notifications.count()

        # Unread chat messages (only messages not sent by the user)
        unread_chat_count = ChatMessage.objects.filter(
            room__participants=self.request.user,
            read=False
        ).exclude(sender=self.request.user).count()

        # Favorite project IDs for the current user
        favorite_ids = self.request.user.favorite_projects.values_list('project_id', flat=True)

        context.update({
            'all_categories': Category.objects.all(),
            'user_skills': {s.name.lower() for s in self.request.user.profile.skills.all()},
            'selected_categories': self.request.GET.get('categories', '').split(','),
            'selected_skills': self.request.GET.get('skills', '').split(','),
            'current_query': self.request.GET.get('q', ''),
            'time_sort': self.request.GET.get('time_sort', ''),
            'match_sort': self.request.GET.get('match_sort', ''),
            'notifications': unread_notifications,
            'notifications_count': notifications_count,
            'chat_rooms': ChatRoom.objects.filter(participants=self.request.user).order_by('-created_at'),
            'unread_chat_count': unread_chat_count,
            'favorite_ids': list(favorite_ids)
        })

        # Retrieve recommended projects and annotate them with application status
        recommended = recommend_projects_for_user(self.request.user, top_n=9)
        for project in recommended:
            user_app = project.applications.filter(applicant=self.request.user).first()
            project.application_status = user_app.status if user_app else None

        context['recommended_projects'] = recommended

        return context




class ChatListView(LoginRequiredMixin, ListView):
    model = ChatRoom
    template_name = 'chat/chat_list.html'
    context_object_name = 'chat_rooms'
    paginate_by = 10

    def get_queryset(self):
        return ChatRoom.objects.filter(participants=self.request.user).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        chat_data = []
        for room in context['chat_rooms']:
            other_user = room.participants.exclude(id=user.id).first()
            last_message = room.messages.last()
            unread_count = room.messages.filter(read=False).exclude(sender=user).count()
            chat_data.append({
                'room': room,
                'other_user': other_user,
                'last_message': last_message,
                'unread_count': unread_count,
            })
        context['chat_data'] = chat_data
        context['chat_folders'] = ChatFolder.objects.filter(user=user)
        return context


class MarkChatReadView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        room_id = data.get('room_id')
        if room_id:
            room = get_object_or_404(ChatRoom, id=room_id)
            updated = room.messages.filter(read=False).exclude(sender=request.user).update(read=True)
            return JsonResponse({'success': True, 'updated': updated})
        return JsonResponse({'success': False, 'error': 'No room_id provided'})


from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
class FolderCreateView(LoginRequiredMixin, CreateView):
    model = ChatFolder
    fields = ['name']
    success_url = reverse_lazy('chat_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        self.object = form.save()
        return JsonResponse({'success': True, 'folder_id': self.object.id, 'name': self.object.name})

    def form_invalid(self, form):
        return JsonResponse({'success': False, 'error': form.errors.as_json()})

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        form = self.get_form_class()(data)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class FolderUpdateView(LoginRequiredMixin, UpdateView):
    model = ChatFolder
    fields = ['name']
    template_name = 'chat/folder_form.html'
    success_url = reverse_lazy('chat_list')

    def get_queryset(self):
        return ChatFolder.objects.filter(user=self.request.user)


class FolderDeleteView(LoginRequiredMixin, DeleteView):
    model = ChatFolder
    template_name = 'chat/folder_confirm_delete.html'
    success_url = reverse_lazy('chat_list')

    def get_queryset(self):
        return ChatFolder.objects.filter(user=self.request.user)


@csrf_exempt
def add_chat_to_folder(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        folder_id = data.get('folder_id')
        chat_id = data.get('chat_id')
        if folder_id and chat_id:
            folder = get_object_or_404(ChatFolder, id=folder_id, user=request.user)
            room = get_object_or_404(ChatRoom, id=chat_id)
            folder.chats.add(room)
            return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid data'})


def unread_chat_count(request):
    if request.user.is_authenticated:
        count = ChatMessage.objects.filter(
            room__participants=request.user,
            read=False
        ).exclude(sender=request.user).count()
        return {'unread_chat_count': count}
    return {'unread_chat_count': 0}


class NotificationsListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'marketplace/notifications_list.html'
    context_object_name = 'notifications'
    paginate_by = 10

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')


class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'marketplace/project_detail.html'
    context_object_name = 'project'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
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
        if ProjectApplication.objects.filter(project=project, applicant=request.user).exists():
            messages.info(request, "You have already applied to this project.")
            return redirect('project-detail', pk=project.id)
        form = ProjectApplicationForm()
        context = {'project': project, 'form': form}
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
            project.application_count = project.applications.count()
            project.save(update_fields=['application_count'])
            messages.success(request, 'Your application has been submitted successfully!')
            Notification.objects.create(
                user=project.owner,
                message=f"{request.user.username} sent a request to join your project '{project.title}'.",
                link=reverse('project-detail', kwargs={'pk': project.pk})
            )
            return redirect('project-detail', pk=project.id)
        else:
            context = {'project': project, 'form': form}
            return render(request, 'marketplace/apply_project.html', context)


class DeleteApplicationView(LoginRequiredMixin, DeleteView):
    model = ProjectApplication
    template_name = 'marketplace/application_confirm_delete.html'
    success_url = reverse_lazy('my-requests')

    def get_queryset(self):
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
        qs = Project.objects.filter(owner=self.request.user)
        # Time sorting: defaults to 'recent'; if 'old' is specified, order ascending by created_at.
        time_sort = self.request.GET.get('time_sort', 'recent')
        if time_sort == 'old':
            qs = qs.order_by('created_at')
        else:
            qs = qs.order_by('-created_at')
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add all categories for filtering (if needed in the template)
        context['all_categories'] = Category.objects.all()
        # Pass the current sorting parameter to the template
        context['time_sort'] = self.request.GET.get('time_sort', 'recent')
        # Also include any status filter if needed (e.g., active/inactive)
        context['status'] = self.request.GET.get('status', '')
        return context


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
        print("🟢 Form is valid. Attempting to create project.")
        skill_ids = form.cleaned_data.get('skills_required', [])
        selected_skills = Skill.objects.filter(id__in=skill_ids)
        if len(selected_skills) < 1:
            messages.error(self.request, "Please select at least 1 skills.")
            print("❌ ERROR: Less than 1 skills selected.")
            return self.render_to_response(self.get_context_data(form=form))
        form.instance.owner = self.request.user
        self.object = form.save(commit=False)
        self.object.save()
        form.save_m2m()
        self.object.skills_required.set(selected_skills)
        categories_str = self.request.POST.get('categories', '')
        print(f"📌 Categories received: {categories_str}")
        if categories_str:
            category_ids = [cid.strip() for cid in categories_str.split(',') if cid.strip()]
            categories_qs = Category.objects.filter(id__in=category_ids)
            self.object.category.set(categories_qs)
        languages_str = self.request.POST.get('languages', '')
        print(f"📌 Languages received: {languages_str}")
        if languages_str:
            language_ids = [lid.strip() for lid in languages_str.split(',') if lid.strip()]
            language_objs = Language.objects.filter(id__in=language_ids)
            self.object.languages.set(language_objs)
        roles_str = self.request.POST.get('required_roles', '')
        print(f"📌 Required Roles received: {roles_str}")
        if roles_str:
            role_ids = [rid.strip() for rid in roles_str.split(',') if rid.strip()]
            role_objs = RequiredRole.objects.filter(id__in=role_ids)
            self.object.required_roles.set(role_objs)
        messages.success(self.request, "✅ Project created successfully!")
        return redirect(self.object.get_absolute_url())

    def form_invalid(self, form):
        print("❌ ERROR: Form is invalid.")
        print("🔴 Form Errors:", form.errors.as_json())
        messages.error(self.request, "Something went wrong. Please check your inputs.")
        return self.render_to_response(self.get_context_data(form=form))


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'marketplace/project_update.html'
    context_object_name = 'project'

    def get_queryset(self):
        return Project.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['skill_categories'] = SkillsCategory.objects.prefetch_related('subcategories__skills').all()
        context['available_categories'] = Category.objects.all()
        context['min_selections'] = 1
        context['languages'] = Language.objects.all()
        context['required_roles'] = RequiredRole.objects.all()
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
        skill_ids = form.cleaned_data.get('skills_required', [])
        selected_skills = Skill.objects.filter(id__in=skill_ids)
        if len(selected_skills) < 1:
            messages.error(self.request, 'Please select at least 1 skills.')
            context = self.get_context_data()
            return self.render_to_response(context)
        form.instance.owner = self.request.user
        self.object = form.save(commit=False)
        self.object.save()
        form.save_m2m()
        self.object.skills_required.set(selected_skills)
        categories_str = self.request.POST.get('categories', '')
        if categories_str:
            category_ids = [cid.strip() for cid in categories_str.split(',') if cid.strip()]
            categories_qs = Category.objects.filter(id__in=category_ids)
            self.object.category.set(categories_qs)
        languages_str = self.request.POST.get('languages', '')
        if languages_str:
            language_ids = [lid.strip() for lid in languages_str.split(',') if lid.strip()]
            language_objs = Language.objects.filter(id__in=language_ids)
            self.object.languages.set(language_objs)
        roles_str = self.request.POST.get('required_roles', '')
        if roles_str:
            role_ids = [rid.strip() for rid in roles_str.split(',') if rid.strip()]
            role_objs = RequiredRole.objects.filter(id__in=role_ids)
            self.object.required_roles.set(role_objs)
        messages.success(self.request, "Project updated successfully!")
        accepted_applications = self.object.applications.filter(status='ACCEPTED')
        for application in accepted_applications:
            Notification.objects.create(
                user=application.applicant,
                message=f"The project '{self.object.title}' has been updated. Please review the latest changes.",
                link=self.object.get_absolute_url()
            )
        return redirect(self.object.get_absolute_url())


class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Project
    template_name = 'marketplace/project_confirm_delete.html'
    success_url = reverse_lazy('my-projects')

    def get_queryset(self):
        return Project.objects.filter(owner=self.request.user)


class ProjectToggleView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        project = get_object_or_404(Project, pk=self.kwargs['pk'], owner=request.user)
        project.is_active = not project.is_active
        project.save()
        return redirect('my-projects')


@login_required
@require_POST
def toggle_favorite(request):
    project_id = request.POST.get('project_id')
    if not project_id:
        return JsonResponse({'success': False, 'error': 'No project_id provided'})
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Project not found'})

    favorite, created = FavoriteProject.objects.get_or_create(user=request.user, project=project)
    if not created:
        favorite.delete()
        is_favorite = False
    else:
        is_favorite = True
    return JsonResponse({'success': True, 'is_favorite': is_favorite})


class FavoritesListView(LoginRequiredMixin, ListView):
    template_name = 'marketplace/favorites.html'
    context_object_name = 'projects'
    paginate_by = 10

    def get_queryset(self):
        queryset = Project.objects.filter(
            favorited_by__user=self.request.user
        ).distinct()
        for project in queryset:
            user_app = project.applications.filter(applicant=self.request.user).first()
            project.user_application = user_app
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        favorite_ids = self.request.user.favorite_projects.values_list('project_id', flat=True)
        context['favorite_ids'] = list(favorite_ids)
        context['favorite_page'] = True
        return context


from projects.recommendation import recommend_projects_for_user

@login_required
def recommended_projects(request):
    user = request.user
    recommended = recommend_projects_for_user(user, top_n=5)
    return render(request, 'marketplace', {'recommended_projects': recommended})


def user_profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    user_projects = Project.objects.filter(owner=profile_user)
    context = {
        'profile_user': profile_user,
        'projects_count': user_projects.count(),
        'projects': user_projects,
    }
    return render(request, 'marketplace/project_profile.html', context)


@login_required
def update_application(request, pk, status):
    application = get_object_or_404(ProjectApplication, pk=pk, project__owner=request.user)
    previous_status = application.status
    application.status = status
    application.save()
    if previous_status != status:
        Notification.objects.create(
            user=application.applicant,
            message=f"Your application to {application.project.title} has been {status.lower()}",
            link=reverse('project-detail', kwargs={'pk': application.project.pk})
        )
    return redirect('project-detail', pk=application.project.pk)


from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from .models import User, ChatRoom, ChatMessage



@login_required
def chat_view(request, user_id):
    # Get the other user to chat with.
    other_user = get_object_or_404(User, id=user_id)
    current_user = request.user

    # Try to find an existing chat room with exactly these two participants.
    rooms = ChatRoom.objects.filter(participants=current_user).filter(participants=other_user)
    room = None
    for r in rooms:
        if r.participants.count() == 2:
            room = r
            break

    # If no room exists, create one.
    if not room:
        room = ChatRoom.objects.create()
        room.participants.add(current_user, other_user)

    # Mark messages as read for the current user.
    # Only update messages not sent by the current user.
    updated = room.messages.filter(read=False).exclude(sender=current_user).update(read=True)

    # (Optional) Broadcast updated unread count to the current user's chat list.
    channel_layer = get_channel_layer()
    unread_count = room.messages.filter(read=False).exclude(sender=current_user).count()
    async_to_sync(channel_layer.group_send)(
        f"chatlist_{current_user.id}",
        {
            "type": "chatlist_update",
            "data": {
                "chat_id": room.id,
                "unread_count": unread_count,
                "last_message": "",
                "timestamp": ""
            }
        }
    )

    # Get all chat messages ordered by timestamp.
    chat_messages = room.messages.all().order_by('timestamp')

    context = {
        'room': room,
        'other_user': other_user,
        'chat_messages': chat_messages,
        'room_id': room.id,
    }
    return render(request, 'chat/chat.html', context)


@login_required
def chat_messages(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    current_user = request.user
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
        return ProjectApplication.objects.filter(applicant=self.request.user).order_by('-applied_at')


@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.read = True
    notification.save()
    return redirect('notifications_list')


@login_required
def mark_all_notifications_read(request):
    Notification.objects.filter(user=request.user, read=False).update(read=True)
    return redirect('notifications_list')

