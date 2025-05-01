from django.urls import path
from . import views
from .views import home, profile, RegisterView, EditProfileView, ResendCodeView, settings_view, CustomPasswordResetView, CustomPasswordResetConfirmView, SetPasswordView
from django.contrib.auth.views import PasswordResetDoneView, PasswordResetCompleteView

urlpatterns = [
    path('', home, name='users-home'),
    path('register/', RegisterView.as_view(), name='users-register'),
    path('profile/', profile, name='users-profile'),
    path('profile/edit/', EditProfileView.as_view(), name='users-edit-profile'),

    path('search_interests/', views.search_interests, name='search_interests'),
    path('search_skills/', views.search_skills, name='search_skills'),

    path('about/', views.about, name='users-about'),
    path('terms/', views.terms, name='users-terms'),
    path('services/', views.services, name='users-services'),
    path('contact/', views.contact_view, name='contact'),

    path('resend-code/', ResendCodeView.as_view(), name='resend-code'),
    path('privacy-policy/', views.privacyPolicy, name='privacy-policy'),

    path('user/<str:username>/', views.user_profile, name='user-profile'),
    path('settings/', settings_view, name='user-settings'),
    path('password-reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', PasswordResetDoneView.as_view(template_name='users/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', PasswordResetCompleteView.as_view(template_name='users/password_reset_complete.html'), name='password_reset_complete'),
    path('set-password/', SetPasswordView.as_view(), name='set-password'),

]
