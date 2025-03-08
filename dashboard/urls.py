from django.urls import path
from .views import (
    dashboard_view,
    manage_users_view,
    manage_projects_view,
    bulk_user_action_view,
    edit_user_view,
    edit_project_view,
    delete_project_view,
)

urlpatterns = [
    path('', dashboard_view, name='dashboard-home'),
    path('users/', manage_users_view, name='dashboard-users'),
    path('users/bulk/', bulk_user_action_view, name='dashboard-bulk-user-action'),
    path('users/edit/<int:user_id>/', edit_user_view, name='dashboard-edit-user'),
    path('projects/', manage_projects_view, name='dashboard-projects'),
    path('projects/edit/<int:project_id>/', edit_project_view, name='dashboard-edit-project'),
    path('projects/delete/<int:project_id>/', delete_project_view, name='dashboard-delete-project'),
]
