from django.urls import path
from . import views

urlpatterns = [
    # Other URL patterns
    path('project/create/', views.project_create, name='project-create'),  # Update with hyphen style
    path('project/<int:project_id>/', views.project_detail, name='project_detail'),
    path('project/<int:project_id>/edit/', views.project_edit, name='project_edit'),
    path('project/<int:project_id>/delete/', views.project_delete, name='project_delete'),
    path('', views.project_list, name='marketplace'),
]
