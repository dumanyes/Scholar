import json
from datetime import timedelta
import numpy as np
from numpy.linalg import norm
from sklearn.feature_extraction.text import TfidfVectorizer
from django.utils import timezone
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Count, Sum, Case, When
from django.views import View
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import (
    ListView, DetailView, UpdateView,
    DeleteView, CreateView
)
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from projects.models import (
    Project, Category, ProjectApplication,
    ChatMessage, ChatRoom
)
from projects.recommendation import rank_projects_with_faiss
from .models import (
    Notification, Skill, Language, RequiredRole,
    ChatFolder, FavoriteProject, PinnedProject,
    ProjectInvitation, User
)
from .forms import ProjectApplicationForm, ProjectForm


def compute_faiss_match(project, user):
    """
    Computes a FAISS-based similarity percentage between a project's profile and a user's profile.
    """
    project_text = " ".join([skill.name for skill in project.skills_required.all()])
    project_text += " " + (project.project_mission or "")
    project_text += " " + (project.project_objectives or "")
    project_text += " " + (project.description or "")
    project_text += " " + " ".join([cat.name for cat in project.category.all()])

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

        # --- Filter by Language ---
        languages_param = self.request.GET.get('languages', '')
        if languages_param:
            language_ids = [lid.strip() for lid in languages_param.split(',') if lid.strip()]
            if language_ids:
                queryset = queryset.filter(languages__id__in=language_ids).distinct()

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
        request = self.request

        unread_notifications = request.user.notifications.filter(read=False).order_by('-created_at')
        unread_chat_count = ChatMessage.objects.filter(
            room__participants=request.user, read=False
        ).exclude(sender=request.user).count()

        context.update({
            'all_categories': Category.objects.all(),
            'user_skills': {s.name.lower() for s in request.user.profile.skills.all()},
            'selected_categories': request.GET.get('categories', '').split(','),
            'selected_skills': request.GET.get('skills', '').split('||'),
            'selected_languages': request.GET.get('languages', '').split(','),
            'current_query': request.GET.get('q', ''),
            'time_sort': request.GET.get('time_sort', ''),
            'time_filter': request.GET.get('time_filter', ''),
            'date_from': request.GET.get('date_from', ''),
            'date_to': request.GET.get('date_to', ''),
            'notifications': unread_notifications,
            'notifications_count': unread_notifications.count(),
            'chat_rooms': ChatRoom.objects.filter(participants=request.user).order_by('-created_at'),
            'unread_chat_count': unread_chat_count,
            'favorite_ids': list(request.user.favorite_projects.values_list('project_id', flat=True)),
            'skills': Skill.objects.all(),
            'languages': Language.objects.all(),
        })

        recommended = recommend_projects_for_user(request.user)

        if not request.user.profile.categories.exists():
            context['recommended_projects'] = []
            context['recommended_projects_message'] = "To see recommended projects, indicate your research areas."
            return context

        categories_param = request.GET.get('categories', '')
        skills_param = request.GET.get('skills', '')
        languages_param = request.GET.get('languages', '')
        q = request.GET.get('q', '')
        time_filter = request.GET.get('time_filter', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')

        if categories_param:
            cat_ids = [cid.strip() for cid in categories_param.split(',') if cid.strip()]
            recommended = [p for p in recommended if any(str(cat.id) in cat_ids for cat in p.category.all())]

        if skills_param:
            skill_names = [s.strip() for s in skills_param.split('||') if s.strip()]
            recommended = [p for p in recommended if any(skill.name in skill_names for skill in p.skills_required.all())]

        if languages_param:
            lang_ids = [lid.strip() for lid in languages_param.split(',') if lid.strip()]
            recommended = [p for p in recommended if any(str(lang.id) in lang_ids for lang in p.languages.all())]

        if q:
            recommended = [p for p in recommended if q.lower() in (
                (p.title or '') + (p.description or '') + (p.project_mission or '') + (p.project_objectives or '')
            ).lower()]

        if time_filter:
            now = timezone.now()
            if time_filter == 'last_24_hours':
                cutoff = now - timedelta(days=1)
                recommended = [p for p in recommended if p.created_at >= cutoff]
            elif time_filter == 'last_week':
                cutoff = now - timedelta(weeks=1)
                recommended = [p for p in recommended if p.created_at >= cutoff]
            elif time_filter == 'last_month':
                cutoff = now - timedelta(days=30)
                recommended = [p for p in recommended if p.created_at >= cutoff]
            elif time_filter == 'last_year':
                cutoff = now - timedelta(days=365)
                recommended = [p for p in recommended if p.created_at >= cutoff]
            elif time_filter == 'custom' and date_from and date_to:
                recommended = [p for p in recommended if date_from <= p.created_at.date().isoformat() <= date_to]

        for project in recommended:
            app = project.applications.filter(applicant=request.user).first()
            project.application_status = app.status if app else None

        recommended_paginator = Paginator(recommended, 10)
        page = self.request.GET.get('rec_page')
        try:
            recommended_page = recommended_paginator.page(page)
        except PageNotAnInteger:
            recommended_page = recommended_paginator.page(1)
        except EmptyPage:
            recommended_page = recommended_paginator.page(recommended_paginator.num_pages)

        context['recommended_projects'] = recommended_page
        context['recommended_is_paginated'] = recommended_paginator.num_pages > 1

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
        qs = Notification.objects.filter(user=self.request.user)

        period = self.request.GET.get('period', 'all')
        now = timezone.now()
        today = now.date()

        week_start = today - timedelta(days=today.weekday())

        if period == 'today':
            qs = qs.filter(created_at__date=today)
        elif period == 'this_week':
            qs = qs.filter(created_at__date__gte=week_start, created_at__date__lte=today)
        elif period == 'older':

            qs = qs.exclude(created_at__date__gte=week_start)


        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # pass active tab to template
        ctx['active_period'] = self.request.GET.get('period', 'all')
        return ctx



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
            application.resume = form.cleaned_data.get('resume')
            application.resume_link = form.cleaned_data.get('resume_link')
            application.save()

            # Send to applicant
            send_notification(
                user=request.user,
                message=f"🔔 You have successfully applied to the project '{project.title}'.",
                link=reverse('project-detail', kwargs={'pk': project.pk})
            )

            # Send to owner if needed (AND if it's not the same user)
            owner_profile = project.owner.profile
            if project.owner != request.user and owner_profile.notify_on_application and owner_profile.email_notifications:
                send_notification(
                    user=project.owner,
                    message=f"🔔 {request.user.username} has applied to your project '{project.title}'.",
                    link=reverse('project-detail', kwargs={'pk': project.pk})
                )

            # WebSocket обновление
            channel_layer = get_channel_layer()
            for user in [request.user, project.owner]:
                async_to_sync(channel_layer.group_send)(
                    f"marketplace_{user.id}",
                    {
                        "type": "send_update",
                        "data": {
                            "notifications_count": Notification.objects.filter(user=user, read=False).count(),
                            "unread_chat_count": ChatMessage.objects.filter(
                                room__participants=user, read=False
                            ).exclude(sender=user).count()
                        }
                    }
                )

            messages.success(request, "Your application has been submitted successfully!")
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
        pinned_projects = PinnedProject.objects.filter(user=self.request.user)\
            .select_related('project').order_by('-pinned_at')[:5]
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
        # ensure self.object exists for get_context_data
        self.object = None

        # preprocess the hidden M2M fields only if non-empty
        post_data = request.POST.copy()
        for field in ['languages', 'skills_required', 'required_roles', 'category']:
            raw = post_data.get(field, '')
            if raw.strip():
                post_data.setlist(field, raw.split(','))
        self.request.POST = post_data

        # build & validate the form
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            # DEBUG: log full errors to server-side log
            import logging
            logging.debug("ProjectCreateView form errors: %s", form.errors.as_json())

            # SURFACE each field error back to the user as a flash message
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")

            return self.form_invalid(form)

    def form_valid(self, form):

        skill_ids = form.cleaned_data.get('skills_required', [])
        selected_skills = Skill.objects.filter(id__in=skill_ids)
        if len(selected_skills) < 1:
            messages.error(self.request, "Please select at least 1 skill.")
            return self.render_to_response(self.get_context_data(form=form))
        form.instance.is_active = True
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
        initial['category']   = ",".join(str(cat.id) for cat in project.category.all())
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
        for field in ['languages', 'skills_required', 'required_roles', 'category']:
            if field in post_data:
                post_data.setlist(field, post_data.get(field, '').split(','))
        request.POST = post_data
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.owner = self.request.user
        self.object.save()
        form.save_m2m()
        self.object.category.set(form.cleaned_data['category'])
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
    template_name      = 'marketplace/favorites.html'
    context_object_name = 'projects'
    paginate_by        = 10

    def get_queryset(self):
        qs = list(Project.objects.filter(favorited_by__user=self.request.user).distinct())
        if qs:
            recommended_order, faiss_scores = rank_projects_with_faiss(qs, self.request.user)
            id_to_proj = {p.id: p for p in qs}
            ordered = []
            for pk in recommended_order:
                proj = id_to_proj.get(pk)
                if proj:
                    proj.faiss_score = faiss_scores.get(pk, 0)
                    ordered.append(proj)

            return ordered

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['favorite_ids']   = list(self.request.user.favorite_projects.values_list('project_id', flat=True))
        ctx['applied_count']  = ProjectApplication.objects.filter(applicant=self.request.user).count()
        ctx['all_categories'] = Category.objects.all()
        ctx['favorite_page']  = True
        return ctx


from projects.recommendation import recommend_projects_for_user

@login_required
def recommended_projects(request):
    user = request.user
    recommended = recommend_projects_for_user(user)
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
    old_status = application.status

    application.status = status
    application.save()

    if old_status != status:
        applicant = application.applicant
        applicant_profile = applicant.profile

        # Check settings before sending notification
        if applicant_profile.notify_on_application_status_change and applicant_profile.email_notifications:
            message = f"Your application to '{application.project.title}' has been {status.lower()}."
            link = reverse('project-detail', kwargs={'pk': application.project.pk})

            send_notification(user=applicant, message=message, link=link)

        # WebSocket real-time update (always update panel, even if no notification)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"marketplace_{applicant.id}",
            {
                "type": "send_update",
                "data": {
                    "notifications_count": Notification.objects.filter(user=applicant, read=False).count(),
                    "unread_chat_count": ChatMessage.objects.filter(
                        room__participants=applicant, read=False
                    ).exclude(sender=applicant).count(),
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
    model               = ProjectApplication
    template_name       = 'marketplace/my_requests.html'
    context_object_name = 'applications'
    paginate_by         = 10

    def get_queryset(self):
        qs     = ProjectApplication.objects.filter(applicant=self.request.user)
        status = self.request.GET.get('status')
        if status in ('pending','accepted','rejected'):
            qs = qs.filter(status=status.upper())
        # sort:
        sort = self.request.GET.get('sort')
        if sort == 'oldest':
            qs = qs.order_by('applied_at')
        else:  # newest first
            qs = qs.order_by('-applied_at')
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        base = ProjectApplication.objects.filter(applicant=self.request.user)
        ctx.update({
            'pending_count':  base.filter(status='PENDING').count(),
            'accepted_count': base.filter(status='ACCEPTED').count(),
            'rejected_count': base.filter(status='REJECTED').count(),
            'total_count':    base.count(),
        })
        # re-echo the current filters up to the template
        ctx['current_status'] = self.request.GET.get('status','all')
        ctx['current_sort']   = self.request.GET.get('sort','newest')
        return ctx



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
    recommended = recommend_projects_for_user(request.user)
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

def recommend_users_for_project(project, top_n=20):
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

    # Получаем только пользователей, которые разрешили приглашения
    recommended_users = ProjectCreateView().get_recommended_users(project, top_n=20)
    recommended_users = [user for user in recommended_users if getattr(user.profile, 'allow_project_invites', True)]

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

from projects.utils import send_notification

@require_POST
@login_required
def invite_user_to_project(request, project_id, user_id):
    project = get_object_or_404(Project, pk=project_id, owner=request.user)
    invited_user = get_object_or_404(User, pk=user_id)

    # Проверка: разрешено ли приглашать этого пользователя
    if not invited_user.profile.allow_project_invites:
        return JsonResponse({'success': False, 'message': 'User does not accept project invitations.'}, status=403)

    # Пытаемся создать приглашение
    invitation, created = ProjectInvitation.objects.get_or_create(
        project=project,
        invited_user=invited_user,
        defaults={'invited_by': request.user}
    )

    if created:
        # Отправить уведомление приглашённому пользователю, если включены настройки
        if invited_user.profile.allow_project_invites and invited_user.profile.email_notifications:
            send_notification(
                user=invited_user,
                message=f"You have been invited to join the project '{project.title}' by {request.user.username}.",
                link=reverse('project-detail', kwargs={'pk': project.pk}),
                notification_type="general"
            )

        # Отправить уведомление себе
        send_notification(
            user=request.user,
            message=f"Invitation sent to {invited_user.username} for project '{project.title}'.",
            link=reverse('project-detail', kwargs={'pk': project.pk}),
            notification_type="general"
        )

        messages.success(request, f"Invitation successfully sent to {invited_user.username}.")
        return JsonResponse({'success': True, 'message': f"Invitation sent to {invited_user.username}."})

    else:
        # Приглашение уже существует
        return JsonResponse({'success': False, 'message': 'User has already been invited.'})

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