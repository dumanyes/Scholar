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


# views.py
class RegisterView(View):
    form_class = RegisterForm
    template_name = 'users/register.html'
    steps = ['personal', 'verify', 'password', 'avatar', 'professional']
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
        session_data = request.session.get('registration_data', {})

        if step == 0:  # Personal Info
            form = self.form_class(request.POST)
            if form.is_valid():
                # Initialize session data as dictionary
                request.session['registration_data'] = {
                    'first_name': form.cleaned_data['first_name'],
                    'last_name': form.cleaned_data['last_name'],
                    'username': form.cleaned_data['username'],
                    'email': form.cleaned_data['email']
                }
                # Generate and send verification code
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


        elif step == 1:  # Verification

            entered_code = request.POST.get('verification_code')

            stored_code = request.session.get('verification_code')

            if str(entered_code) == str(stored_code):
                return redirect(f"{reverse('users-register')}?step=2")

            messages.error(request, 'Invalid verification code')

            return redirect(f"{reverse('users-register')}?step=1")

        if step == 2:  # Password Step

            password1 = request.POST.get('password1')

            password2 = request.POST.get('password2')

            if password1 and password1 == password2:
                # Create a copy of session data to modify

                updated_data = session_data.copy()

                updated_data['password'] = password1

                # Update session data atomically

                request.session['registration_data'] = updated_data

                request.session.modified = True

                return redirect(f"{reverse('users-register')}?step=3")

            messages.error(request, 'Passwords do not match')

            return redirect(f"{reverse('users-register')}?step=2")

        elif step == 3:  # Avatar
            avatar = request.FILES.get('avatar')
            if avatar:
                request.session['registration_data']['avatar'] = avatar
            return redirect(f"{reverse('users-register')}?step=4")



        elif step == 4:  # Skills selection

            skills_data = json.loads(request.POST.get('selected_skills', '[]'))

            if len(skills_data) < 5:
                messages.error(request, 'Please select at least 5 skills')

                return redirect(f"{reverse('users-register')}?step=4")

            # Process skills

            skills = []

            for skill_name in skills_data:
                skill, created = Skill.objects.get_or_create(

                    name=skill_name,

                    defaults={'created_by': request.user if request.user.is_authenticated else None}

                )

                skills.append(skill.id)

            request.session['registration_data']['skills'] = skills

            return redirect(f"{reverse('users-register')}?step=5")


        elif step == 5:  # Interests selection

            interests_data = json.loads(request.POST.get('selected_interests', '[]'))

            if len(interests_data) < 5:
                messages.error(request, 'Please select at least 5 interests')

                return redirect(f"{reverse('users-register')}?step=5")

            # Process interests

            interests = []

            for interest_name in interests_data:
                interest, created = Interest.objects.get_or_create(

                    name=interest_name,

                    defaults={'created_by': request.user if request.user.is_authenticated else None}

                )

                interests.append(interest.id)

            request.session['registration_data']['interests'] = interests

            return self.finalize_registration(request)
        return self.get(request)

    def get_step_context(self, request, step):
        context = {
            'step': step,
            'progress': ((step + 1) / len(self.steps)) * 100,
            'form': self.form_class()
        }

        if step == 1:  # Verification
            context['email'] = request.session.get('registration_data', {}).get('email', '')

        elif step == 2:  # Password
            context['password_form'] = True

        elif step == 3:  # Avatar
            context['avatar_form'] = True

        elif step == 4:  # Skills
            context['skills'] = Skill.objects.filter(approved=True)
            context['min_selections'] = self.min_selections


        elif step == 5:  # Interests
            context['interests'] = Interest.objects.filter(approved=True)
            context['min_selections'] = self.min_selections

        return context

    def finalize_registration(self, request):
        data = request.session.get('registration_data', {})

        if 'password' not in data:
            logger.error('Password missing during final registration')
            messages.error(request, 'Registration failed: Password not found')
            return redirect(f"{reverse('users-register')}?step=2")

        try:
            # Create user
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                first_name=data['first_name'],
                last_name=data['last_name']
            )

            # Get the existing profile (created by signal) and update it
            profile = user.profile
            if 'avatar' in data:
                profile.avatar.save(data['avatar'].name, data['avatar'])

            # Add skills and interests from session data
            profile.skills.set(data.get('skills', []))
            profile.interests.set(data.get('interests', []))

            # Cleanup session
            del request.session['registration_data']
            del request.session['verification_code']

            messages.success(request, 'Registration completed successfully!')
            return redirect('login')

        except KeyError as e:
            logger.error(f'Missing registration data: {str(e)}')
            messages.error(request, f'Missing information: {str(e)}')
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

def services(request):
    return render(request, 'users/services.html')

def contact(request):
    return render(request, 'users/contact.html')