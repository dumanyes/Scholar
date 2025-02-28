
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
    chat_view, chat_messages, MyRequestsView, DeleteApplicationView, withdraw_application, ChatListView,
    NotificationsListView, FolderCreateView, FolderDeleteView, FolderUpdateView, MarkChatReadView, add_chat_to_folder,
    toggle_favorite, FavoritesListView,
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

    path('chats/', ChatListView.as_view(), name='chat_list'),
    path('notifications/', NotificationsListView.as_view(), name='notifications_list'),

    path('folder/create/', FolderCreateView.as_view(), name='folder_create'),
    path('folder/<int:pk>/update/', FolderUpdateView.as_view(), name='folder_update'),
    path('folder/<int:pk>/delete/', FolderDeleteView.as_view(), name='folder_delete'),
    path('chat/mark_read/', MarkChatReadView.as_view(), name='mark_chat_read'),
    path('chat/add_to_folder/', add_chat_to_folder, name='add_chat_to_folder'),

    path('notifications/mark/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('toggle_favorite/', toggle_favorite, name='toggle-favorite'),
    path('favorites/', FavoritesListView.as_view(), name='favorites'),
]
