# users/middleware.py
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
