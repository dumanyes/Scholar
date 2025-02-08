import os
import logging
import requests
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


class RegisterView(View):
    form_class = RegisterForm
    template_name = 'users/register.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(to='/')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return render(request, self.template_name, {'form': self.form_class()})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            user = form.save()

            # Check if a profile already exists for the user
            if not hasattr(user, 'profile'):
                Profile.objects.create(user=user)

            messages.success(request, 'Account created successfully')
            return redirect('login')

        return render(request, self.template_name, {'form': form})


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