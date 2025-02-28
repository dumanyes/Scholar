
from django.urls import path

from . import views
from .views import (
    MarketplaceView,
    ProjectDetailView,
    ApplyProjectView,
    MyProjectsView,
    ProjectCreateView,
    ProjectUpdateView,
    ProjectDeleteView,
    ProjectToggleView,
    user_profile,
    update_application,
    chat_view, chat_messages, MyRequestsView, DeleteApplicationView, withdraw_application,
)

urlpatterns = [

    path('', MarketplaceView.as_view(), name='marketplace'),
    path('project/<int:pk>/', ProjectDetailView.as_view(), name='project-detail'),
    path('my-projects/', MyProjectsView.as_view(), name='my-projects'),
    path('project/create/', ProjectCreateView.as_view(), name='project-create'),
    path('project/<int:pk>/update/', ProjectUpdateView.as_view(), name='project-update'),
    path('project/<int:pk>/delete/', ProjectDeleteView.as_view(), name='project-delete'),
    path('project/<int:pk>/toggle/', ProjectToggleView.as_view(), name='project-toggle'),
    path('profile/<str:username>/', user_profile, name='user-profile'),
    path('application/<int:pk>/<str:status>/', update_application, name='update-application'),
    path('chat/<int:user_id>/', chat_view, name='chat'),
    path('chat-messages/<int:user_id>/', chat_messages, name='chat_messages'),
    path('my-requests/', MyRequestsView.as_view(), name='my-requests'),

    path('project/<int:project_id>/apply/', ApplyProjectView.as_view(), name='apply-project'),
    path('application/<int:pk>/delete/', DeleteApplicationView.as_view(), name='delete-application'),
    path('project/<int:project_id>/withdraw/', withdraw_application, name='withdraw-application'),

    path('profile/<str:username>/', user_profile, name='project-user-profile'),


]
