from django.urls import reverse
from django.utils import timezone
from users.models import Profile

class UpdateLastOnlineMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                profile = request.user.profile
            except Profile.DoesNotExist:
                profile = Profile.objects.create(user=request.user)
            profile.last_online = timezone.now()
            profile.save(update_fields=['last_online'])
        return self.get_response(request)

from django.utils import translation

class ProfileLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and hasattr(request.user, 'profile'):
            # lang = request.user.profile.preferred_language or 'en'
            lang = 'en'  # фикс — устанавливаем язык по умолчанию
            translation.activate(lang)
            request.LANGUAGE_CODE = lang
        response = self.get_response(request)
        return response

from django.dispatch import receiver
from allauth.account.signals import user_logged_in
from django.shortcuts import redirect

@receiver(user_logged_in)
def check_user_password(sender, request, user, **kwargs):
    if not user.has_usable_password():
        request.session['redirect_after_login'] = True

class ForceSetPasswordMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if (not request.user.has_usable_password()
                and not request.path.startswith(reverse('set-password'))
                and not request.path.startswith(reverse('logout'))):
                return redirect('set-password')

        response = self.get_response(request)
        return response