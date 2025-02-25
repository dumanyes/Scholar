
import os
import requests
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.decorators import login_required
from .forms import LoginForm, UpdateUserForm, UpdateProfileForm
from .models import Profile
from projects.models import Skill, Interest
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
        # You can add additional context as needed
    })




from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from .forms import UpdateUserForm, UpdateProfileForm
from projects.models import Category, SkillsCategory, Skill
from cities_light.models import Country, City
from users.models import University  # Adjust the import if your University model is located elsewhere

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from random import randint
from projects.models import Skill, Category, SkillsCategory
from cities_light.models import Country, City
from users.models import University
from .forms import UpdateUserForm, UpdateProfileForm

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
            'skill_categories': SkillsCategory.objects.prefetch_related('subcategories', 'subcategories__skills').all(),
            'countries': Country.objects.all(),
            'cities': City.objects.all(),
            'universities': University.objects.all(),
            'min_selections': self.min_selections,
            # When not in email-verification mode, no need to show the code input.
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
                        'skill_categories': SkillsCategory.objects.prefetch_related('subcategories', 'subcategories__skills').all(),
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
                        'skill_categories': SkillsCategory.objects.prefetch_related('subcategories', 'subcategories__skills').all(),
                        'countries': Country.objects.all(),
                        'cities': City.objects.all(),
                        'universities': University.objects.all(),
                        'min_selections': self.min_selections,
                        'email_verification_required': True,
                    }
                    return render(request, self.template_name, context)
            # Save user and profile
            user = user_form.save()
            profile = profile_form.save(commit=False)
            # Process location fields.
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
                        'skill_categories': SkillsCategory.objects.prefetch_related('subcategories', 'subcategories__skills').all(),
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
            profile_form.save_m2m()  # Save many-to-many relationships
            messages.success(request, "Profile updated successfully!")
            return redirect('users-profile')
        else:
            messages.error(request, "Please correct the errors below.")
        context = {
            'user_form': user_form,
            'profile_form': profile_form,
            'available_categories': Category.objects.all(),
            'skill_categories': SkillsCategory.objects.prefetch_related('subcategories', 'subcategories__skills').all(),
            'countries': Country.objects.all(),
            'cities': City.objects.all(),
            'universities': University.objects.order_by('name'),
            'min_selections': self.min_selections,
        }
        return render(request, self.template_name, context)



logger = logging.getLogger(__name__)

import os
import json
import logging
from random import randint
from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from .forms import RegisterForm
from projects.models import (
    User,
    SkillsCategory,
    SkillsSubCategory,
    Skill,
)

logger = logging.getLogger(__name__)


class RegisterView(View):
    form_class = RegisterForm
    template_name = 'users/register.html'
    steps = ['personal', 'verify', 'password', 'skills']
    min_selections = 5

    def dispatch(self, request, *args, **kwargs):
        """Check if user is already authenticated"""
        if request.user.is_authenticated:
            return redirect('/')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        """Handle GET requests - display the appropriate registration step"""
        step = int(request.GET.get('step', 0))
        context = self.get_step_context(request, step)
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST requests - process form data for each registration step"""
        step = int(request.POST.get('step', 0))
        registration_data = request.session.get('registration_data', {})

        # STEP 0: Personal Info
        if step == 0:
            form = self.form_class(request.POST)
            # Keep only personal info fields
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

                # Generate and send verification code
                code = str(randint(100000, 999999))
                request.session['verification_code'] = code
                try:
                    send_mail(
                        'ScholarHub Verification Code',
                        f'Your verification code: {code}',
                        settings.DEFAULT_FROM_EMAIL,
                        [form.cleaned_data['email']],
                        fail_silently=False,
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
            # Keep only password fields
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
                # Parse and validate selected skills
                skills_data = json.loads(request.POST.get('selected_skills', '[]'))
                selected_skills = Skill.objects.filter(id__in=skills_data)

                if len(selected_skills) < self.min_selections:
                    messages.error(request, f'Please select at least {self.min_selections} skills')
                    context = {
                        'step': step,
                        'skill_categories': SkillsCategory.objects.prefetch_related(
                            'subcategories',
                            'subcategories__skills'
                        ).all(),
                        'min_selections': self.min_selections,
                        'progress': ((step + 1) / len(self.steps)) * 100
                    }
                    return render(request, self.template_name, context)

                registration_data['skills'] = list(selected_skills.values_list('id', flat=True))
                request.session['registration_data'] = registration_data
                return self.finalize_registration(request)

            except json.JSONDecodeError:
                messages.error(request, 'Invalid skills data provided')
            except Exception as e:
                logger.error(f"Skills selection error: {str(e)}")
                messages.error(request, 'An error occurred while processing your skills selection')

            context = {
                'step': step,
                'skill_categories': SkillsCategory.objects.prefetch_related(
                    'subcategories',
                    'subcategories__skills'
                ).all(),
                'min_selections': self.min_selections,
                'progress': ((step + 1) / len(self.steps)) * 100
            }
            return render(request, self.template_name, context)

        return self.get(request)

    def get_step_context(self, request, step):
        """Prepare context data for each registration step"""
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
            context['skill_categories'] = SkillsCategory.objects.prefetch_related(
                'subcategories',
                'subcategories__skills'
            ).all()
            context['min_selections'] = self.min_selections

        return context

    def finalize_registration(self, request):
        """Complete the registration process and create the user account"""
        data = request.session.get('registration_data', {})

        if 'password' not in data:
            messages.error(request, 'Registration failed: Password not found')
            return redirect(f"{reverse('users-register')}?step=2")

        try:
            # Create the user account
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                first_name=data['first_name'],
                last_name=data['last_name']
            )

            # Set up the user's profile
            profile = user.profile

            # Add selected skills to profile
            if 'skills' in data:
                profile.skills.set(data['skills'])

            # Clean up session data
            request.session.pop('registration_data', None)
            request.session.pop('verification_code', None)

            messages.success(request, 'Registration completed successfully!')
            return redirect('login')

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
        return super().form_valid(form)


class ResetPasswordView(SuccessMessageMixin, PasswordResetView):
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.html'
    success_message = "We've emailed you instructions for setting your password."
    success_url = reverse_lazy('users-home')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request
        context['domain'] = request.get_host()
        context['protocol'] = 'https' if request.is_secure() else 'http'
        return context

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except Exception as e:
            logger.error(f"Password reset email failed: {str(e)}")
            messages.error(self.request, "Failed to send email. Check your email settings.")
            return self.form_invalid(form)



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