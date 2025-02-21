import json
import os
import logging
from django.urls import reverse
from random import randint

import requests
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordChangeView
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.views import View
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.conf import settings
from requests import request

from projects.models import User
from .forms import RegisterForm, LoginForm, UpdateUserForm, UpdateProfileForm
from .models import Profile, Skill, Interest
from cities_light.models import Country, City

# Logger setup
logger = logging.getLogger(__name__)

# ORCID OAuth Constants (from environment variables)
ORCID_CLIENT_ID = os.getenv('ORCID_CLIENT_ID')
ORCID_CLIENT_SECRET = os.getenv('ORCID_CLIENT_SECRET')
ORCID_REDIRECT_URI = os.getenv('ORCID_REDIRECT_URI')


def home(request):
    return render(request, 'users/home.html')


@login_required
def profile(request):
    return render(request, 'users/profile.html', {
        'profile': request.user.profile,
        'country': request.user.profile.country,
        'skills': request.user.profile.skills.all()
    })


def get_cities(request, country_id):
    cities = City.objects.filter(country_id=country_id).values('id', 'name')
    return JsonResponse({'cities': list(cities)})


class EditProfileView(View):
    template_name = 'users/edit_profile.html'

    def get(self, request):
        user_form = UpdateUserForm(instance=request.user)
        profile_form = UpdateProfileForm(instance=request.user.profile)

        current_country = request.user.profile.country
        cities = City.objects.filter(country=current_country) if current_country else []

        context = {
            'user_form': user_form,
            'profile_form': profile_form,
            'countries': Country.objects.all(),
            'cities': cities,
            'selected_country': current_country.id if current_country else None,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        user_form = UpdateUserForm(request.POST, instance=request.user)
        profile_form = UpdateProfileForm(request.POST, request.FILES, instance=request.user.profile)

        try:
            if user_form.is_valid() and profile_form.is_valid():
                user = user_form.save()
                profile = profile_form.save(commit=False)

                # Process interests
                interest_names = request.POST.getlist('interests')
                interests = [
                    Interest.objects.get_or_create(name=name.strip(), defaults={'created_by': user, 'approved': False})[
                        0] for name in interest_names if name.strip()]
                profile.interests.set(interests)

                # Process skills
                profile.skills.set(profile_form.cleaned_data['skills'])
                profile.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('users-profile')

        except Exception as e:
            logger.error(f'Profile update failed: {e}')
            messages.error(request, f'Error saving profile: {str(e)}')

        selected_country = request.POST.get('country')
        cities = City.objects.filter(country_id=selected_country) if selected_country else []

        context = {
            'user_form': user_form,
            'profile_form': profile_form,
            'countries': Country.objects.all(),
            'cities': cities,
            'selected_country': selected_country,
        }
        return render(request, self.template_name, context)


from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from random import randint
import json
import logging

from .forms import RegisterForm
from .models import Skill, Interest

logger = logging.getLogger(__name__)

class RegisterView(View):
    form_class = RegisterForm
    template_name = 'users/register.html'
    # We only want 5 steps total
    steps = ['personal', 'verify', 'password', 'skills', 'interests']
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

        # Step 0: Personal Info
        if step == 0:
            form = self.form_class(request.POST)
            # Only keep personal-info fields
            personal_fields = ['first_name', 'last_name', 'username', 'email', 'birthdate', 'terms_and_conditions']
            for field in list(form.fields.keys()):
                if field not in personal_fields:
                    form.fields.pop(field)

            if form.is_valid():
                # Save personal info to session
                registration_data.update({
                    'first_name': form.cleaned_data['first_name'],
                    'last_name': form.cleaned_data['last_name'],
                    'username': form.cleaned_data['username'],
                    'email': form.cleaned_data['email'],
                    'birthdate': (
                        form.cleaned_data['birthdate'].strftime('%Y-%m-%d')
                        if form.cleaned_data['birthdate']
                        else None
                    ),
                })
                request.session['registration_data'] = registration_data

                # Generate & email a verification code
                code = str(randint(100000, 999999))
                request.session['verification_code'] = code
                send_mail(
                    'ScholarHub Verification Code',
                    f'Your verification code: {code}',
                    settings.DEFAULT_FROM_EMAIL,
                    [form.cleaned_data['email']],
                    fail_silently=False,
                )
                return redirect(f"{reverse('users-register')}?step=1")
            else:
                messages.error(request, "Please fix the errors below.")
                context = {
                    'form': form,
                    'step': step,
                    'progress': ((step + 1) / len(self.steps)) * 100
                }
                return render(request, self.template_name, context)

        # Step 1: Email Verification
        elif step == 1:
            entered_code = request.POST.get('verification_code')
            stored_code = request.session.get('verification_code')
            if str(entered_code) == str(stored_code):
                return redirect(f"{reverse('users-register')}?step=2")
            messages.error(request, 'Invalid verification code')
            context = {
                'step': step,
                'email': registration_data.get('email', ''),
                'progress': ((step + 1) / len(self.steps)) * 100
            }
            return render(request, self.template_name, context)

        # Step 2: Password Setup
        elif step == 2:
            form = self.form_class(request.POST)
            # Keep only password1 & password2 fields
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

        # Step 3: Skills
        elif step == 3:
            skills_data = json.loads(request.POST.get('selected_skills', '[]'))
            if len(skills_data) < self.min_selections:
                messages.error(request, f'Please select at least {self.min_selections} skills')
                context = {
                    'step': step,
                    'skills': Skill.objects.filter(approved=True),
                    'min_selections': self.min_selections,
                    'progress': ((step + 1) / len(self.steps)) * 100
                }
                return render(request, self.template_name, context)

            registration_data['skills'] = [
                Skill.objects.get_or_create(name=s, defaults={'created_by': None})[0].id
                for s in skills_data
            ]
            request.session['registration_data'] = registration_data
            return redirect(f"{reverse('users-register')}?step=4")

        # Step 4: Interests
        elif step == 4:
            interests_data = json.loads(request.POST.get('selected_interests', '[]'))
            if len(interests_data) < self.min_selections:
                messages.error(request, f'Please select at least {self.min_selections} interests')
                context = {
                    'step': step,
                    'interests': Interest.objects.filter(approved=True),
                    'min_selections': self.min_selections,
                    'progress': ((step + 1) / len(self.steps)) * 100
                }
                return render(request, self.template_name, context)

            registration_data['interests'] = [
                Interest.objects.get_or_create(name=i, defaults={'created_by': None})[0].id
                for i in interests_data
            ]
            request.session['registration_data'] = registration_data

            # Done. Finalize
            return self.finalize_registration(request)

        # If none of the above matched, fallback to GET logic
        return self.get(request)

    def get_step_context(self, request, step):
        """
        Prepare template context depending on the step.
        """
        context = {
            'step': step,
            'progress': ((step + 1) / len(self.steps)) * 100
        }

        if step == 0:
            # Full form for personal info
            context['form'] = self.form_class()

        elif step == 1:
            # Show email address for verification
            context['email'] = request.session.get('registration_data', {}).get('email', '')

        elif step == 2:
            # Provide a form only with password fields
            password_form = self.form_class()
            for field in list(password_form.fields.keys()):
                if field not in ['password1', 'password2']:
                    password_form.fields.pop(field)
            context['form'] = password_form
            context['password_form'] = True

        elif step == 3:
            # Skills selection
            context['skills'] = Skill.objects.filter(approved=True)
            context['min_selections'] = self.min_selections

        elif step == 4:
            # Interests selection
            context['interests'] = Interest.objects.filter(approved=True)
            context['min_selections'] = self.min_selections

        return context

    def finalize_registration(self, request):
        """
        Create the user and finalize the registration.
        """
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
            # For demonstration, attach skills & interests to user.profile
            profile = user.profile
            profile.skills.set(data.get('skills', []))
            profile.interests.set(data.get('interests', []))

            # Clean up session
            if 'registration_data' in request.session:
                del request.session['registration_data']
            if 'verification_code' in request.session:
                del request.session['verification_code']

            messages.success(request, 'Registration completed successfully!')
            return redirect('login')

        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
            return redirect(reverse('users-register'))


# class VerifyEmailView(View):
#     def get(self, request):
#         return render(request, 'users/verify_email.html')
#
#     def post(self, request):
#         entered_code = request.POST.get('verification_code')
#         stored_code = request.session.get('verification_code')
#
#         if str(entered_code) == str(stored_code):
#             # Create user account
#             data = request.session.get('registration_data')
#             user = User.objects.create_user(
#                 username=data['username'],
#                 email=data['email'],
#                 password=data['password'],
#                 first_name=data['first_name'],
#                 last_name=data['last_name']
#             )
#             # Create profile
#             Profile.objects.create(user=user)
#
#             # Cleanup session
#             del request.session['verification_code']
#             del request.session['registration_data']
#
#             messages.success(request, 'Account created successfully!')
#             return redirect('login')
#
#         messages.error(request, 'Invalid verification code')
#         return redirect('verify-email')
#

# In views.py
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
        return super().form_valid(form)


class ResetPasswordView(SuccessMessageMixin, PasswordResetView):
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.html'
    success_message = "We've emailed you instructions for setting your password."
    success_url = reverse_lazy('users-home')


class ChangePasswordView(SuccessMessageMixin, PasswordChangeView):
    template_name = 'users/change_password.html'
    success_message = "Successfully Changed Your Password"
    success_url = reverse_lazy('users-home')


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

def contact(request):
    return render(request, 'users/contact.html')

def privacyPolicy(request):
    return render(request, 'users/privacy_policy.html')