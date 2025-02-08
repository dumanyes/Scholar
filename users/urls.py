from django.urls import path
from . import views
from .views import home, profile, RegisterView, EditProfileView

urlpatterns = [
    path('', home, name='users-home'),
    path('register/', RegisterView.as_view(), name='users-register'),
    path('profile/', profile, name='users-profile'),
    path('profile/edit/', EditProfileView.as_view(), name='users-edit-profile'),  # New edit profile page
    path('get_cities/', views.get_cities, name='get_cities'),
    path('get_cities/<int:country_id>/', views.get_cities, name='get_cities'),
    path('search_interests/', views.search_interests, name='search_interests'),
    path('search_skills/', views.search_skills, name='search_skills'),

    path('about/', views.about, name='users-about'),
    path('services/', views.services, name='users-services'),
    path('contact/', views.contact, name='users-contact'),
]
