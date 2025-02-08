from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from users import views
from users.views import CustomLoginView, ResetPasswordView, ChangePasswordView
from users.forms import LoginForm

urlpatterns = [
    path('admin/', admin.site.urls),
    path('marketplace/', include('projects.urls')),  # Marketplace routes (projects app)
    path('oauth/', include('social_django.urls', namespace='social')),  # Social auth routes

    path('', include('users.urls')),  # User management paths
    # path('accounts/', include('allauth.urls')),

    path('login/', CustomLoginView.as_view(
        redirect_authenticated_user=True,
        template_name='users/login.html',
        authentication_form=LoginForm
    ), name='login'),

    path('logout/', auth_views.LogoutView.as_view(template_name='users/logout.html'), name='logout'),

    path('password-reset/', ResetPasswordView.as_view(), name='password_reset'),

    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='users/password_reset_confirm.html'),
         name='password_reset_confirm'),

    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='users/password_reset_complete.html'),
         name='password_reset_complete'),

    path('password-change/', ChangePasswordView.as_view(), name='password_change'),

    path('orcid/authorize/', views.orcid_authorize, name='orcid-authorize'),
    path('orcid/callback/', views.get_orcid_id_from_orcid_oauth, name='orcid-callback'),

    path('profile/', views.profile, name='users-profile'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # Serve media files in dev
