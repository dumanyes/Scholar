from django.contrib import admin
from .models import Profile, Skill, Interest, University
from cities_light.models import Country

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'approved', 'created_by')
    search_fields = ('name',)
    list_filter = ('approved',)

@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display = ('name', 'approved', 'created_by')
    search_fields = ('name',)
    list_filter = ('approved',)

# Register Profile model
admin.site.register(Profile)
admin.site.register(University)


# No need to register Country again as it is already registered by cities_light
