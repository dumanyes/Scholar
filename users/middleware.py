# middleware.py
from django.utils import timezone

class UpdateLastOnlineMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            profile = request.user.profile
            profile.last_online = timezone.now()
            profile.save(update_fields=['last_online'])
        return self.get_response(request)
