from urllib import request
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, UpdateView, DeleteView, CreateView, ListView
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.db.models import Q, OuterRef, Subquery, CharField, Case, When, Count, Exists, Sum
import json
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin

from .forms import ProjectApplicationForm, ProjectForm
from .models import (
    Notification, Skill, Language, RequiredRole,
    ChatFolder, ChatRoom, FavoriteProject, Project, ProjectApplication,
    Category, ChatMessage, User, ProjectInvitation, PinnedProject
)
from projects.models import Project, ProjectApplication, Category, ChatMessage, ChatRoom
from projects.recommendation import rank_projects_with_faiss, recommend_projects_for_user

# ---------------------------
# Helper functions for reverse recommendations
# ---------------------------
from sklearn.feature_extraction.text import TfidfVectorizer
from numpy.linalg import norm
import numpy as np

def compute_faiss_match(project, user):
    """
    Computes a FAISS-based similarity percentage between a project's profile and a user's profile.
    """
    # Build the project profile text
    project_text = " ".join([skill.name for skill in project.skills_required.all()])
    project_text += " " + (project.project_mission or "")
    project_text += " " + (project.project_objectives or "")
    project_text += " " + (project.description or "")
    project_text += " " + " ".join([cat.name for cat in project.category.all()])

    # Build the user profile text
    user_skills_text = " ".join([skill.name for skill in user.profile.skills.all()])
    bio_text = user.profile.bio or ""
    user_categories_text = " ".join([cat.name for cat in user.profile.categories.all()])
    user_text = " ".join([user_skills_text, bio_text, user_categories_text])

    vectorizer = TfidfVectorizer()
    texts = [project_text, user_text]
    try:
        vectors = vectorizer.fit_transform(texts).toarray()
        if norm(vectors[0]) == 0 or norm(vectors[1]) == 0:
            return 0.0
        cos_sim = np.dot(vectors[0], vectors[1]) / (norm(vectors[0]) * norm(vectors[1]) + 1e-8)
    except Exception:
        cos_sim = 0.0
    return round(cos_sim * 100, 2)

def get_matched_skills(project, user):
    """
    Returns a list of (skill_id, skill_name) tuples that are required by the project
    and also present in the user's profile.
    """
    required_skills = {skill.name.lower() for skill in project.skills_required.all()}
    user_skills = [(skill.id, skill.name) for skill in user.profile.skills.all()]
    return [(skill_id, skill_name) for skill_id, skill_name in user_skills if skill_name.lower() in required_skills]

# ---------------------------
# Views
# ---------------------------

class MarketplaceView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'marketplace/marketplace.html'
    context_object_name = 'projects'

    def get_queryset(self):
        queryset = Project.objects.filter(is_active=True)
        # --- Filter by Clickable Categories ---
        categories_param = self.request.GET.get('categories', '')
        if categories_param:
            cat_ids = [cid.strip() for cid in categories_param.split(',') if cid.strip()]
            if cat_ids:
                queryset = queryset.filter(category__id__in=cat_ids).distinct()
        # --- Filter by Skills ---
        skills_param = self.request.GET.get('skills', '')
        if skills_param:
            skill_names = [s.strip() for s in skills_param.split('||') if s.strip()]
            if skill_names:
                queryset = queryset.filter(skills_required__name__in=skill_names).distinct()
        # --- Text Search Filtering ---
        q = self.request.GET.get('q', '')
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q) |
                Q(project_mission__icontains=q) |
                Q(project_objectives__icontains=q)
            )
        # --- Time-Based Filtering ---
        time_filter = self.request.GET.get('time_filter', '')
        if time_filter:
            now = timezone.now()
            if time_filter == 'last_24_hours':
                cutoff = now - timedelta(days=1)
                queryset = queryset.filter(created_at__gte=cutoff)
            elif time_filter == 'last_week':
                cutoff = now - timedelta(weeks=1)
                queryset = queryset.filter(created_at__gte=cutoff)
            elif time_filter == 'last_month':
                cutoff = now - timedelta(days=30)
                queryset = queryset.filter(created_at__gte=cutoff)
            elif time_filter == 'last_year':
                cutoff = now - timedelta(days=365)
                queryset = queryset.filter(created_at__gte=cutoff)
            elif time_filter == 'custom':
                date_from = self.request.GET.get('date_from')
                date_to = self.request.GET.get('date_to')
                if date_from and date_to:
                    queryset = queryset.filter(created_at__range=[date_from, date_to])
        # --- Ordering ---
        time_sort = self.request.GET.get('time_sort', '')
        if time_sort == 'recent':
            queryset = queryset.order_by('-created_at')
        elif time_sort == 'old':
            queryset = queryset.order_by('created_at')
        else:
            projects_list = list(queryset)
            if projects_list:
                recommended_order, faiss_scores = rank_projects_with_faiss(projects_list, self.request.user)
                self.faiss_scores = faiss_scores
                ordering = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(recommended_order)])
                queryset = queryset.filter(pk__in=recommended_order).order_by(ordering)
                projects_with_score = list(queryset)
                for project in projects_with_score:
                    project.faiss_score = self.faiss_scores.get(project.id, 0)
                return projects_with_score
            else:
                queryset = queryset.order_by('-created_at')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        unread_notifications = self.request.user.notifications.filter(read=False).order_by('-created_at')
        notifications_count = unread_notifications.count()
        unread_chat_count = ChatMessage.objects.filter(
            room__participants=self.request.user,
            read=False
        ).exclude(sender=self.request.user).count()
        favorite_ids = self.request.user.favorite_projects.values_list('project_id', flat=True)
        context.update({
            'all_categories': Category.objects.all(),
            'user_skills': {s.name.lower() for s in self.request.user.profile.skills.all()},
            'selected_categories': self.request.GET.get('categories', '').split(','),
            'selected_skills': self.request.GET.get('skills', '').split('||'),
            'current_query': self.request.GET.get('q', ''),
            'time_sort': self.request.GET.get('time_sort', ''),
            'time_filter': self.request.GET.get('time_filter', ''),
            'date_from': self.request.GET.get('date_from', ''),
            'date_to': self.request.GET.get('date_to', ''),
            'notifications': unread_notifications,
            'notifications_count': notifications_count,
            'chat_rooms': ChatRoom.objects.filter(participants=self.request.user).order_by('-created_at'),
            'unread_chat_count': unread_chat_count,
            'favorite_ids': list(favorite_ids)
        })
        context['skills'] = Skill.objects.all()
        # Recommended projects section
        recommended = recommend_projects_for_user(self.request.user, top_n=9)
        for project in recommended:
            user_app = project.applications.filter(applicant=self.request.user).first()
            project.application_status = user_app.status if user_app else None
        context['recommended_projects'] = recommended
        if not self.request.user.profile.categories.exists():
            context['recommended_projects'] = []
            context['recommended_projects_message'] = (
                "To see the recommended projects, you need to indicate your preferred research areas"
            )
        else:
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
        form = ProjectApplicationForm(project=project)
        context = {'project': project, 'form': form}
        return render(request, 'marketplace/apply_project.html', context)

    def post(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        if ProjectApplication.objects.filter(project=project, applicant=request.user).exists():
            messages.info(request, "You have already applied to this project.")
            return redirect('project-detail', pk=project.id)

        form = ProjectApplicationForm(request.POST, request.FILES, project=project)

        if form.is_valid():
            application = form.save(commit=False)
            application.project = project
            application.applicant = request.user
            application.status = 'PENDING'

            # ✅ Must assign these manually
            application.resume = form.cleaned_data.get('resume')
            application.resume_link = form.cleaned_data.get('resume_link')

            print("DEBUG RESUME FILE:", application.resume)  # Optional debug
            print("DEBUG RESUME LINK:", application.resume_link)

            application.save()

            # Optional: check if file was saved
            print("Saved File URL:", application.resume.url if application.resume else 'No file')

            messages.success(request, 'Your application has been submitted successfully!')
            return redirect('project-detail', pk=project.id)

        return render(request, 'marketplace/apply_project.html', {'project': project, 'form': form})



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


from django.views.generic import ListView
from django.db.models import Q, Count, Sum
from django.contrib.auth.mixins import LoginRequiredMixin
from projects.models import Project, Category
from .models import PinnedProject

class MyProjectsView(LoginRequiredMixin, ListView):
    template_name = 'marketplace/my_projects.html'
    context_object_name = 'projects'
    paginate_by = 10

    def get_queryset(self):
        qs = Project.objects.filter(owner=self.request.user)

        # Search query filtering
        query = self.request.GET.get('q')
        if query:
            qs = qs.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query)
            )
        # Status filtering
        status = self.request.GET.get('status')
        if status == 'active':
            qs = qs.filter(is_active=True)
        elif status == 'inactive':
            qs = qs.filter(is_active=False)
        # Category filtering
        categories = self.request.GET.get('categories')
        if categories:
            category_ids = [int(cid) for cid in categories.split(',') if cid]
            qs = qs.filter(category__id__in=category_ids).distinct()
        # Date range filtering
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        if start_date and end_date:
            qs = qs.filter(created_at__date__range=[start_date, end_date])
        # Sorting (default: newest first)
        sort = self.request.GET.get('sort', '-created_at')
        qs = qs.order_by(sort)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_projects = self.get_queryset()

        # Pinned projects: last 5 pinned by the user
        pinned_projects = PinnedProject.objects.filter(user=self.request.user)\
            .select_related('project').order_by('-pinned_at')[:5]

        # Analytics / Statistics
        stats = all_projects.aggregate(
            active_count=Count('id', filter=Q(is_active=True)),
            total_views=Sum('view_count'),
            total_applications=Sum('application_count')
        )

        context.update({
            'pinned_projects': [pp.project for pp in pinned_projects],
            'active_count': stats['active_count'] or 0,
            'inactive_count': all_projects.count() - (stats['active_count'] or 0),
            'total_views': stats['total_views'] or 0,
            'total_applications': stats['total_applications'] or 0,
            'all_categories': Category.objects.all(),
            'selected_categories': self.request.GET.get('categories', ''),
            'status': self.request.GET.get('status', ''),
            'q': self.request.GET.get('q', ''),
            'start_date': self.request.GET.get('start_date', ''),
            'end_date': self.request.GET.get('end_date', ''),
            'sort': self.request.GET.get('sort', '-created_at'),
        })
        return context



class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'marketplace/project_create.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models import Category, Language, RequiredRole
        context['skills'] = Skill.objects.all()
        context['available_categories'] = Category.objects.all()
        context['languages'] = Language.objects.all()
        context['required_roles'] = RequiredRole.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        post_data = request.POST.copy()
        for field in ['languages', 'skills_required', 'required_roles', 'categories']:
            if field in post_data:
                post_data.setlist(field, post_data.get(field, '').split(','))
        self.request.POST = post_data
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        skill_ids = form.cleaned_data.get('skills_required', [])
        selected_skills = Skill.objects.filter(id__in=skill_ids)
        if len(selected_skills) < 1:
            messages.error(self.request, "Please select at least 1 skill.")
            return self.render_to_response(self.get_context_data(form=form))
        form.instance.owner = self.request.user
        self.object = form.save(commit=False)
        self.object.save()
        form.save_m2m()
        self.object.skills_required.set(selected_skills)
        category_ids = form.cleaned_data.get('categories', [])
        if category_ids:
            categories_qs = Category.objects.filter(id__in=category_ids)
            self.object.category.set(categories_qs)
        language_ids = form.cleaned_data.get('languages', [])
        if language_ids:
            language_objs = Language.objects.filter(id__in=language_ids)
            self.object.languages.set(language_objs)
        role_ids = form.cleaned_data.get('required_roles', [])
        if role_ids:
            role_objs = RequiredRole.objects.filter(id__in=role_ids)
            self.object.required_roles.set(role_objs)
        messages.success(self.request, "✅ Project created successfully!")
        # Redirect to the reverse recommendation view
        return redirect(reverse('project-recommendations', kwargs={'project_id': self.object.id}))

    def form_invalid(self, form):
        messages.error(self.request, "Something went wrong. Please check your inputs.")
        return self.render_to_response(self.get_context_data(form=form))

    def get_recommended_users(self, project, top_n=20):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        candidates = User.objects.filter(is_active=True).exclude(id=project.owner.id)
        scored_candidates = []
        for user in candidates:
            score = project.get_skill_match(user)
            if score > 0:
                scored_candidates.append((user, score))
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        return [user for user, score in scored_candidates][:top_n]


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'marketplace/project_update.html'


    def get_initial(self):
        initial = super().get_initial()
        project = self.get_object()
        initial['skills_required'] = ",".join(str(skill.id) for skill in project.skills_required.all())
        initial['required_roles'] = ",".join(str(role.id) for role in project.required_roles.all())
        initial['categories'] = ",".join(str(cat.id) for cat in project.category.all())
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        if self.request.method == 'POST':
            post_data = self.request.POST
            try:
                cat_ids = [int(x) for x in post_data.get('categories', '').split(',') if x]
            except Exception:
                cat_ids = []
            try:
                lang_ids = [int(x) for x in post_data.get('languages', '').split(',') if x]
            except Exception:
                lang_ids = []
            try:
                role_ids = [int(x) for x in post_data.get('required_roles', '').split(',') if x]
            except Exception:
                role_ids = []
        else:
            cat_ids = [cat.id for cat in project.category.all()]
            lang_ids = [lang.id for lang in project.languages.all()]
            role_ids = [rl.id for rl in project.required_roles.all()]

        cat_ids = [cat.id for cat in project.category.all()]
        lang_ids = [lang.id for lang in project.languages.all()]
        role_ids = [role.id for role in project.required_roles.all()]

        context.update({
            "selected_categories_list": cat_ids,
            "selected_languages_list": lang_ids,
            "selected_required_roles_list": role_ids,
            "selected_categories": ",".join(map(str, cat_ids)),
            "selected_languages": ",".join(map(str, lang_ids)),
            "selected_required_roles": ",".join(map(str, role_ids)),
        })
        context["available_categories"] = Category.objects.all()
        context["languages"] = Language.objects.all()
        context["required_roles"] = RequiredRole.objects.all()
        context['skills'] = Skill.objects.all()
        context["selected_categories_list"] = cat_ids
        context["selected_languages_list"] = lang_ids
        context["selected_required_roles_list"] = role_ids
        context["selected_categories"] = ",".join(str(x) for x in cat_ids)
        context["selected_languages"] = ",".join(str(x) for x in lang_ids)
        context["selected_required_roles"] = ",".join(str(x) for x in role_ids)
        return context

    def post(self, request, *args, **kwargs):
        post_data = request.POST.copy()
        for field in ['languages', 'skills_required', 'required_roles', 'categories']:
            if field in post_data:
                post_data.setlist(field, post_data.get(field, '').split(','))
        request.POST = post_data
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.owner = self.request.user
        self.object.save()
        form.save_m2m()
        self.object.category.set(form.cleaned_data.get('categories', []))
        self.object.languages.set(form.cleaned_data.get('languages', []))
        self.object.required_roles.set(form.cleaned_data.get('required_roles', []))
        messages.success(self.request, "✅ Project updated successfully!")
        return redirect(self.object.get_absolute_url())

    def form_invalid(self, form):
        messages.error(self.request, "Something went wrong while updating.")
        return self.render_to_response(self.get_context_data(form=form))


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
        queryset = Project.objects.filter(favorited_by__user=self.request.user).distinct()
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
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"marketplace_{application.applicant.id}",
            {
                "type": "send_update",
                "data": {
                    "notifications_count": Notification.objects.filter(user=application.applicant, read=False).count(),
                    "unread_chat_count": ChatMessage.objects.filter(room__participants=application.applicant,
                                                                    read=False).exclude(
                        sender=application.applicant).count()
                }
            }
        )

    return redirect('project-detail', pk=application.project.pk)


@login_required
def chat_view(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    current_user = request.user
    rooms = ChatRoom.objects.filter(participants=current_user).filter(participants=other_user)
    room = None
    for r in rooms:
        if r.participants.count() == 2:
            room = r
            break
    if not room:
        room = ChatRoom.objects.create()
        room.participants.add(current_user, other_user)
    updated = room.messages.filter(read=False).exclude(sender=current_user).update(read=True)
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


def search_skills(request):
    query = request.GET.get('query', '')
    skills = Skill.objects.filter(name__icontains=query)[:10].values('id', 'name')
    return JsonResponse({'skills': list(skills)})


@login_required
def view_all_recommended(request):
    recommended = recommend_projects_for_user(request.user, top_n=100)
    context = {'recommended_projects': recommended}
    return render(request, 'marketplace/view-all-recommended.html', context)


from django.http import JsonResponse, HttpResponseRedirect

@login_required
@require_POST
def update_profile_preferences(request):
    skills = request.POST.get("skills", "")
    categories = request.POST.get("categories", "")
    try:
        profile = request.user.profile
        if skills:
            skill_ids = [int(s) for s in skills.split("||") if s]
            profile.skills.set(Skill.objects.filter(id__in=skill_ids))
        else:
            profile.skills.clear()
        if categories:
            category_ids = [int(c) for c in categories.split(",") if c]
            profile.categories.set(Category.objects.filter(id__in=category_ids))
        else:
            profile.categories.clear()
        profile.save()
        if request.is_ajax():
            return JsonResponse({"success": True})
        else:
            return HttpResponseRedirect(reverse('marketplace'))
    except Exception as e:
        if request.is_ajax():
            return JsonResponse({"success": False, "error": str(e)})
        else:
            return HttpResponseRedirect(reverse('marketplace'))


# Reverse recommendation functions

def recommend_users_for_project(project, top_n=20):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    candidates = User.objects.filter(is_active=True).exclude(id=project.owner.id)
    scored_candidates = []
    for user in candidates:
        score = project.get_skill_match(user)
        if score > 0:
            scored_candidates.append((user, score))
    scored_candidates.sort(key=lambda x: x[1], reverse=True)
    return [user for user, score in scored_candidates][:top_n]



@login_required
def project_recommendations_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id, owner=request.user)
    recommended_users = ProjectCreateView().get_recommended_users(project, top_n=20)
    for user in recommended_users:
        user.match_score = project.get_skill_match(user)
        user.faiss_match = compute_faiss_match(project, user)
        user.matched_skills = get_matched_skills(project, user)
        # Проверяем, есть ли уже приглашение для этого пользователя
        user.invited = ProjectInvitation.objects.filter(project=project, invited_user=user).exists()
    context = {
        'project': project,
        'recommended_users': recommended_users,
    }
    return render(request, 'marketplace/project_recommendations.html', context)


@require_POST
@login_required
def invite_user_to_project(request, project_id, user_id):
    # Проверяем, что текущий пользователь является владельцем проекта
    project = get_object_or_404(Project, pk=project_id, owner=request.user)
    invited_user = get_object_or_404(User, pk=user_id)

    # Создаем приглашение (или получаем существующее)
    invitation, created = ProjectInvitation.objects.get_or_create(
        project=project,
        invited_user=invited_user,
        defaults={'invited_by': request.user}
    )

    # Создаем уведомления
    Notification.objects.create(
        user=invited_user,
        message=f"You have been invited to join the project '{project.title}' by {request.user.username}.",
        link=reverse('project-detail', kwargs={'pk': project.id})
    )
    Notification.objects.create(
        user=request.user,
        message=f"Invitation sent to {invited_user.username} for project '{project.title}'.",
        link=reverse('project-detail', kwargs={'pk': project.id})
    )
    messages.success(request, f"Invitation sent to {invited_user.username}.")

    # Возвращаем JSON-ответ для обновления состояния кнопки
    return JsonResponse({'success': True, 'message': f"Invitation sent to {invited_user.username}."})

@require_POST
@login_required
def cancel_invite_user_to_project(request, project_id, user_id):
    project = get_object_or_404(Project, pk=project_id)
    if project.owner != request.user:
        return JsonResponse({'error': 'Not authorized'}, status=403)
    invitation = ProjectInvitation.objects.filter(project=project, invited_user__id=user_id).first()
    if invitation:
        invitation.delete()
        return JsonResponse({'success': True, 'message': 'Invitation cancelled'})
    else:
        return JsonResponse({'error': 'Invitation not found'}, status=404)


# Update views.py toggle_pin_project view
@require_POST
@login_required
def toggle_pin_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    pinned = PinnedProject.objects.filter(user=request.user, project=project)

    if pinned.exists():
        pinned.delete()
        status = 'unpinned'
    else:
        PinnedProject.objects.create(user=request.user, project=project)
        status = 'pinned'

    return JsonResponse({
        'status': status,
        'project_title': project.title,
        'project_pk': project.id
    })