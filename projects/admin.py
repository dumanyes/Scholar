from django.contrib import admin
from .models import Project
admin.site.register(Project)

from .models import Category

admin.site.register(Category)