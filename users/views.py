import os
import requests
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.contrib.auth.views import LoginView
from cities_light.models import Country, City
from django.views.generic import TemplateView, FormView
from users.models import University
from dashboard.forms import ContactForm
from .forms import LoginForm, UpdateUserForm, UpdateProfileForm
from .models import Profile
from projects.models import Interest
import json
from random import randint
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings
import logging
from django.views import View
from django.contrib.auth.models import User
from .forms import RegisterForm
from projects.models import Category, Skill
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.db.models.functions import TruncMonth
from projects.models import Project
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetConfirmView,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy

from django.http import HttpResponse



logger = logging.getLogger(__name__)

ORCID_CLIENT_ID = os.getenv('ORCID_CLIENT_ID')
ORCID_CLIENT_SECRET = os.getenv('ORCID_CLIENT_SECRET')
ORCID_REDIRECT_URI = os.getenv('ORCID_REDIRECT_URI')



def home(request):
    total_researchers = User.objects.count()
    total_projects = Project.objects.filter(is_active=True).count()

    # Top 5 categories by number of projects
    top_categories = Category.objects.annotate(
        count=Count('project')
    ).order_by('-count')[:5]

    # Top 5 most needed skills by number of projects
    most_needed_skills = Skill.objects.annotate(
        count=Count('project')
    ).order_by('-count')[:5]

    # Aggregate monthly new researcher registrations
    registration_data = User.objects.annotate(
        month=TruncMonth('date_joined')
    ).values('month').annotate(count=Count('id')).order_by('month')
    registration_months = [item['month'].strftime('%b') for item in registration_data]
    researcher_counts = [item['count'] for item in registration_data]

    # Aggregate monthly project creations
    project_data = Project.objects.annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(count=Count('id')).order_by('month')
    project_months = [item['month'].strftime('%b') for item in project_data]
    project_counts = [item['count'] for item in project_data]

    context = {
        'total_researchers': total_researchers,
        'total_projects': total_projects,
        'top_categories': top_categories,
        'most_needed_skills': most_needed_skills,
        'registration_months': json.dumps(registration_months),
        'researcher_counts': json.dumps(researcher_counts),
        'project_months': json.dumps(project_months),
        'project_counts': json.dumps(project_counts),
    }
    return render(request, 'users/home.html', context)


@login_required
def profile(request):
    return render(request, 'users/profile.html', {
        'profile': request.user.profile,
        'country': request.user.profile.country,
        'skills': request.user.profile.skills.all(),
        'num_projects': request.user.owned_projects.count(),  # Use owned_projects count
    })

def user_profile(request, username):
    # This view returns the profile for the given username (project owner)
    user = get_object_or_404(User, username=username)
    return render(request, 'users/profile.html', {
        'profile': user.profile,
        'country': user.profile.country,
        'skills': user.profile.skills.all(),
    })

class EditProfileView(View):
    template_name = 'users/edit_profile.html'
    min_selections = 1  # minimum required skills

    def get(self, request):
        user_form = UpdateUserForm(instance=request.user)
        profile_form = UpdateProfileForm(instance=request.user.profile)
        context = {
            'user_form': user_form,
            'profile_form': profile_form,
            'available_categories': Category.objects.all(),
            'skills': Skill.objects.all(),
            'countries': Country.objects.all(),
            'cities': City.objects.all(),
            'universities': University.objects.all(),
            'min_selections': self.min_selections,
            'email_verification_required': False,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        user_form = UpdateUserForm(request.POST, instance=request.user)
        profile_form = UpdateProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            new_email = user_form.cleaned_data.get('email')
            old_email = request.user.email

            if new_email != old_email:
                verification_code = request.POST.get('verification_code')
                expected_code = request.session.get('email_verification_code')
                if not expected_code:
                    # Generate and send verification code.
                    code = str(randint(100000, 999999))
                    request.session['email_verification_code'] = code
                    send_mail("Email Verification",
                              f"Your verification code is: {code}",
                              settings.DEFAULT_FROM_EMAIL,
                              [new_email])
                    messages.info(request,
                        "A verification code has been sent to your new email. Please enter it to confirm the change.")
                    context = {
                        'user_form': user_form,
                        'profile_form': profile_form,
                        'available_categories': Category.objects.all(),
                        'skills': Skill.objects.all(),
                        'countries': Country.objects.all(),
                        'cities': City.objects.all(),
                        'universities': University.objects.all(),
                        'min_selections': self.min_selections,
                        'email_verification_required': True,
                    }
                    return render(request, self.template_name, context)
                elif verification_code != expected_code:
                    messages.error(request, "Verification code is incorrect.")
                    context = {
                        'user_form': user_form,
                        'profile_form': profile_form,
                        'available_categories': Category.objects.all(),
                        'skills': Skill.objects.all(),
                        'countries': Country.objects.all(),
                        'cities': City.objects.all(),
                        'universities': University.objects.all(),
                        'min_selections': self.min_selections,
                        'email_verification_required': True,
                    }
                    return render(request, self.template_name, context)
            user = user_form.save()
            profile = profile_form.save(commit=False)
            country_id = request.POST.get('country')
            city_id = request.POST.get('city')
            profile.country = Country.objects.filter(id=country_id).first() if country_id else None
            profile.city = City.objects.filter(id=city_id).first() if city_id else None

            # Process skills.
            skills_ids = request.POST.get('skills', '')
            if skills_ids:
                skill_ids = [s for s in skills_ids.split(",") if s]
                skills = Skill.objects.filter(id__in=skill_ids)
                if skills.count() < 1:
                    messages.error(request, 'Please select at least 1 skill.')
                    context = {
                        'user_form': user_form,
                        'profile_form': profile_form,
                        'available_categories': Category.objects.all(),
                        'skills': Skill.objects.all(),
                        'countries': Country.objects.all(),
                        'cities': City.objects.all(),
                        'universities': University.objects.all(),
                        'min_selections': self.min_selections,
                    }
                    return render(request, self.template_name, context)
                profile.skills.set(skills)
            else:
                profile.skills.clear()

            # Process categories.
            categories_ids = request.POST.get('categories', '')
            if categories_ids:
                selected_categories = [int(cid) for cid in categories_ids.split(",") if cid]
                profile.categories.set(selected_categories)
            else:
                profile.categories.clear()

            profile.save()
            profile_form.save_m2m()
            messages.success(request, "Profile updated successfully!")
            return redirect('users-profile')
        else:
            messages.error(request, "Please correct the errors below.")
        context = {
            'user_form': user_form,
            'profile_form': profile_form,
            'available_categories': Category.objects.all(),
            'skills': Skill.objects.all(),
            'countries': Country.objects.all(),
            'cities': City.objects.all(),
            'universities': University.objects.order_by('name'),
            'min_selections': self.min_selections,
        }
        return render(request, self.template_name, context)

class RegisterView(View):
    form_class = RegisterForm
    template_name = 'users/register.html'
    steps = ['personal', 'verify', 'password', 'skills', 'research']
    min_selections = 5

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('/')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        step = int(request.GET.get('step', 0))
        context = self.get_step_context(request, step)
        return render(request, self.template_name, context)

    def post(self, request):
        step = int(request.POST.get('step', 0))
        registration_data = request.session.get('registration_data', {})

        # STEP 0: Personal Info
        if step == 0:
            form = self.form_class(request.POST)
            # Оставляем только поля личной информации
            personal_fields = ['first_name', 'last_name', 'username', 'email', 'birthdate', 'terms_and_conditions']
            for field in list(form.fields.keys()):
                if field not in personal_fields:
                    form.fields.pop(field)
            if form.is_valid():
                registration_data.update({
                    'first_name': form.cleaned_data['first_name'],
                    'last_name': form.cleaned_data['last_name'],
                    'username': form.cleaned_data['username'],
                    'email': form.cleaned_data['email'],
                    'birthdate': (form.cleaned_data['birthdate'].strftime('%Y-%m-%d')
                                  if form.cleaned_data['birthdate'] else None),
                })
                request.session['registration_data'] = registration_data

                # Генерация и отправка кода верификации
                code = str(randint(100000, 999999))
                request.session['verification_code'] = code
                try:
                    send_mail(
                        "ScholarHub Verification Code",
                        f'Your verification code: {code}',
                        settings.DEFAULT_FROM_EMAIL,
                        [form.cleaned_data['email']]
                    )
                    return redirect(f"{reverse('users-register')}?step=1")
                except Exception as e:
                    logger.error(f"Failed to send verification email: {str(e)}")
                    messages.error(request, "Failed to send verification email. Please try again.")
                    return redirect(reverse('users-register'))
            else:
                messages.error(request, "Please fix the errors below.")
                context = {
                    'form': form,
                    'step': step,
                    'progress': ((step + 1) / len(self.steps)) * 100
                }
                return render(request, self.template_name, context)

        # STEP 1: Email Verification
        elif step == 1:
            entered_code = request.POST.get('verification_code')
            stored_code = request.session.get('verification_code')
            if not stored_code:
                messages.error(request, 'Verification session expired. Please start over.')
                return redirect(reverse('users-register'))
            if str(entered_code) == str(stored_code):
                return redirect(f"{reverse('users-register')}?step=2")
            messages.error(request, 'Invalid verification code')
            context = {
                'step': step,
                'email': registration_data.get('email', ''),
                'progress': ((step + 1) / len(self.steps)) * 100
            }
            return render(request, self.template_name, context)

        # STEP 2: Password Setup
        elif step == 2:
            form = self.form_class(request.POST)
            password_fields = ['password1', 'password2']
            for field in list(form.fields.keys()):
                if field not in password_fields:
                    form.fields.pop(field)
            if form.is_valid():
                registration_data['password'] = form.cleaned_data['password1']
                request.session['registration_data'] = registration_data
                return redirect(f"{reverse('users-register')}?step=3")
            else:
                messages.error(request, "Please fix the errors below.")
                context = {
                    'form': form,
                    'step': step,
                    'password_form': True,
                    'progress': ((step + 1) / len(self.steps)) * 100
                }
                return render(request, self.template_name, context)

        # STEP 3: Skills Selection
        elif step == 3:
            try:
                skills_data = json.loads(request.POST.get('selected_skills', '[]'))
                selected_skills = Skill.objects.filter(id__in=skills_data)
                if len(selected_skills) < self.min_selections:
                    messages.error(request, f'Please select at least {self.min_selections} skills')
                    context = {
                        'step': step,
                        'skills': Skill.objects.all(),
                        'min_selections': self.min_selections,
                        'progress': ((step + 1) / len(self.steps)) * 100
                    }
                    context["all_skills"] = list(Skill.objects.values("id", "name"))
                    return render(request, self.template_name, context)
                registration_data['skills'] = list(selected_skills.values_list('id', flat=True))
                request.session['registration_data'] = registration_data
                return redirect(f"{reverse('users-register')}?step=4")
            except json.JSONDecodeError:
                messages.error(request, 'Invalid skills data provided')
            except Exception as e:
                logger.error(f"Skills selection error: {str(e)}")
                messages.error(request, 'An error occurred while processing your skills selection')
            context = {
                'step': step,
                'skills': Skill.objects.all(),
                'min_selections': self.min_selections,
                'progress': ((step + 1) / len(self.steps)) * 100
            }
            return render(request, self.template_name, context)

        # STEP 4: Research Areas Selection
        elif step == 4:
            categories_data = request.POST.get('selected_categories', '')
            try:
                category_ids = [int(cid) for cid in categories_data.split(",") if cid]
            except ValueError:
                messages.error(request, "Некорректные данные для областей исследований.")
                from projects.models import Category
                context = {
                    'step': step,
                    'available_categories': Category.objects.all(),
                    'progress': ((step + 1) / len(self.steps)) * 100
                }
                return render(request, self.template_name, context)
            registration_data['categories'] = category_ids
            request.session['registration_data'] = registration_data
            return self.finalize_registration(request)

        return self.get(request)

    def get_step_context(self, request, step):
        context = {
            'step': step,
            'progress': ((step + 1) / len(self.steps)) * 100
        }
        if step == 0:
            context['form'] = self.form_class()
        elif step == 1:
            context['email'] = request.session.get('registration_data', {}).get('email', '')
        elif step == 2:
            password_form = self.form_class()
            for field in list(password_form.fields.keys()):
                if field not in ['password1', 'password2']:
                    password_form.fields.pop(field)
            context['form'] = password_form
            context['password_form'] = True
        elif step == 3:
            context['skills'] = Skill.objects.all()
            context['min_selections'] = self.min_selections
            context['all_skills'] = list(Skill.objects.values("id", "name"))
        elif step == 4:
            from projects.models import Category
            context['available_categories'] = Category.objects.all()
        return context

    def finalize_registration(self, request):
        data = request.session.get('registration_data', {})
        if 'password' not in data:
            messages.error(request, 'Registration failed: Password not found')
            return redirect(f"{reverse('users-register')}?step=2")
        try:
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                first_name=data['first_name'],
                last_name=data['last_name']
            )
            profile = user.profile
            if 'skills' in data:
                profile.skills.set(data['skills'])
            if 'categories' in data:
                profile.categories.set(data['categories'])
            request.session.pop('registration_data', None)
            request.session.pop('verification_code', None)
            messages.success(request, 'Registration completed successfully!')
            return redirect('users-home')
        except Exception as e:
            logger.error(f"Registration failed: {str(e)}")
            messages.error(request, 'Registration failed. Please try again.')
            return redirect(reverse('users-register'))


class ResendCodeView(View):
    def get(self, request):
        email = request.session.get('registration_data', {}).get('email')
        if email:
            verification_code = randint(100000, 999999)
            request.session['verification_code'] = verification_code

            send_mail(
                'ScholarHub Email Verification',
                f'Your new verification code is: {verification_code}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )

            return JsonResponse({'success': True})
        return JsonResponse({'success': True, 'redirect_url': f"{reverse('users-register')}?step=1"})


class CustomLoginView(LoginView):
    form_class = LoginForm

    def form_valid(self, form):
        remember_me = form.cleaned_data.get('remember_me')
        if not remember_me:
            self.request.session.set_expiry(0)
            self.request.session.modified = True

        response = super().form_valid(form)
        if self.request.session.pop('redirect_after_login', False):
            return redirect('set-password')
        return response


def orcid_authorize(request):
    if not ORCID_CLIENT_ID or not ORCID_CLIENT_SECRET:
        return JsonResponse({"error": "ORCID configuration missing"}, status=500)

    orcid_url = "https://orcid.org/oauth/authorize"
    params = {
        'client_id': ORCID_CLIENT_ID,
        'response_type': 'code',
        'scope': '/read-limited',
        'redirect_uri': ORCID_REDIRECT_URI,
    }
    return redirect(f"{orcid_url}?{requests.compat.urlencode(params)}")

def get_orcid_id_from_orcid_oauth(request):
    if 'code' not in request.GET:
        return JsonResponse({"error": "Authorization code missing"}, status=400)

    payload = {
        'client_id': ORCID_CLIENT_ID,
        'client_secret': ORCID_CLIENT_SECRET,
        'code': request.GET['code'],
        'redirect_uri': ORCID_REDIRECT_URI,
        'grant_type': 'authorization_code',
    }
    response = requests.post("https://orcid.org/oauth/token", data=payload, headers={'Accept': 'application/json'})
    if response.status_code != 200:
        return JsonResponse({"error": "Failed to fetch access token"}, status=500)

    orcid_id = response.json().get('orcid-identifier', {}).get('path')
    if not orcid_id:
        return JsonResponse({"error": "ORCID ID not found"}, status=500)

    profile, _ = Profile.objects.get_or_create(user=request.user)
    profile.orcid_id = orcid_id
    profile.save()
    return JsonResponse({"message": "ORCID ID saved successfully", "orcid_id": orcid_id})


def search_interests(request):
    query = request.GET.get('query', '')
    interests = Interest.objects.filter(name__icontains=query)[:10].values('id', 'name')
    return JsonResponse({'interests': list(interests)})


def search_skills(request):
    query = request.GET.get('query', '')
    skills = Skill.objects.filter(name__icontains=query)[:10].values('id', 'name')
    return JsonResponse({'skills': list(skills)})


def about(request):
    return render(request, 'users/about.html')

def terms(request):
    return render(request, 'users/terms.html')

def services(request):
    return render(request, 'users/services.html')

def contact_view(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your message was sent successfully!")
            return redirect("contact")
        else:
            print("❌ Form errors:", form.errors)  # Debug
            messages.error(request, "There was a problem sending your message.")
    else:
        form = ContactForm()
    return render(request, "users/contact.html", {"form": form})


def privacyPolicy(request):
    return render(request, 'users/privacy_policy.html')

class SettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'users/settings.html'


@login_required
def settings_view(request):
    if request.method == 'POST':
        profile = request.user.profile
        profile.allow_project_invites = request.POST.get('allow_project_invites') == 'on'
        profile.email_notifications = request.POST.get('email_notifications') == 'on'
        profile.notify_on_application = request.POST.get('notify_on_application') == 'on'
        profile.notify_on_application_status_change = request.POST.get('notify_on_application_status_change') == 'on'
        profile.notify_on_chat_message = request.POST.get('notify_on_chat_message') == 'on'
        # profile.preferred_language = request.POST.get('preferred_language')
        profile.save()

        request.user.refresh_from_db()
        messages.success(request, "✅ Settings saved successfully.")
        return redirect('users-profile')  # 👈 redirect to profile page

    request.user.refresh_from_db()
    return render(request, 'users/settings.html', {
        'profile': request.user.profile
    })


class CustomPasswordResetView(SuccessMessageMixin, PasswordResetView):
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.html'
    success_message = "We've emailed you instructions for setting your password."
    success_url = reverse_lazy('password_reset_done')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request
        context['domain'] = request.get_host()
        context['protocol'] = 'https' if request.is_secure() else 'http'
        return context

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        user_queryset = form.get_users(email)
        user = next(user_queryset, None)

        if not user:
            return HttpResponse("❌ No user found with that email.")

        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        from django.contrib.auth.tokens import default_token_generator
        from django.urls import reverse
        from django.core.mail import send_mail

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        protocol = 'https' if self.request.is_secure() else 'http'
        domain = self.request.get_host()

        reset_link = f"{protocol}://{domain}{reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})}"

        email_subject = "Password Reset on ScholarHub"
        email_body = f"""
    Hello {user.get_full_name() or user.username},

    You requested a password reset.

    Reset link:
    {reset_link}

    If you did not request this, please ignore.

    Thanks,
    ScholarHub Team
        """

        send_mail(
            subject=email_subject,
            message=email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return super().form_valid(form)

class CustomPasswordResetConfirmView(SuccessMessageMixin, PasswordResetConfirmView):
    template_name = 'users/password_reset_confirm.html'
    success_message = "Your password has been set. You can now log in with your new password."
    success_url = reverse_lazy('login')


class SetPasswordView(LoginRequiredMixin, FormView):
    template_name = 'users/set_password.html'
    form_class = SetPasswordForm
    success_url = reverse_lazy('users-home')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        update_session_auth_hash(self.request, self.request.user)  # ✅ здесь фикс
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'errors': form.errors
            }, status=400)
        return super().form_invalid(form)


