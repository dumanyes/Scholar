# urls.py
from django.urls import path

from . import views
from .views import MarketplaceView, ProjectDetailView, ApplyProjectView, MyProjectsView, ProjectCreateView, \
    ProjectUpdateView, ProjectToggleView

urlpatterns = [
    path('marketplace/', MarketplaceView.as_view(), name='marketplace'),
    path('project/<int:pk>/', ProjectDetailView.as_view(), name='project-detail'),
    path('apply/<int:project_id>/', ApplyProjectView.as_view(), name='apply-project'),

# urls.py
    path('my-projects/', MyProjectsView.as_view(), name='my-projects'),
    path('project/create/', ProjectCreateView.as_view(), name='create-project'),
    path('project/<int:pk>/edit/', ProjectUpdateView.as_view(), name='edit-project'),
    path('project/<int:pk>/toggle/', ProjectToggleView.as_view(), name='toggle-project'),
    path('application/<int:pk>/update/<str:status>/', views.update_application, name='update-application'),

    path('profile/<str:username>/', views.user_profile, name='user-profile'),
    path('chat/<int:user_id>/', views.chat_view, name='chat'),
]