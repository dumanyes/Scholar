from django.urls import path, include
from django.views.generic import RedirectView

from . import views
from .views import home, profile, RegisterView, EditProfileView, ResendCodeView, privacyPolicy

urlpatterns = [
    path('', home, name='users-home'),
    path('register/', RegisterView.as_view(), name='users-register'),
    path('profile/', profile, name='users-profile'),
    path('profile/edit/', EditProfileView.as_view(), name='users-edit-profile'),  # New edit profile page


    path('search_interests/', views.search_interests, name='search_interests'),
    path('search_skills/', views.search_skills, name='search_skills'),

    path('about/', views.about, name='users-about'),
    path('terms/', views.terms, name='users-terms'),
    path('services/', views.services, name='users-services'),
    path('contact/', views.contact, name='users-contact'),

    # path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('resend-code/', ResendCodeView.as_view(), name='resend-code'),
    path('privacy-policy/', views.privacyPolicy, name='privacy-policy'),
    path('password-reset/', include('django.contrib.auth.urls')),

    path('user/<str:username>/', views.user_profile, name='user-profile'),




]
