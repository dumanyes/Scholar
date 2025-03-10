from django.urls import path
from .views import journal_list

urlpatterns = [
    path('journals/', journal_list, name='journal_list'),
]
