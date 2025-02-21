from django.contrib import admin
from .models import Profile, Skill, Interest, University
from cities_light.models import Country

# Existing custom actions for other models...
def approve_skills(modeladmin, request, queryset):
    queryset.update(approved=True)
approve_skills.short_description = "Mark selected skills as approved"

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'approved', 'created_by')
    search_fields = ('name',)
    list_filter = ('approved',)
    actions = [approve_skills]

@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display = ('name', 'approved', 'created_by')
    search_fields = ('name',)
    list_filter = ('approved',)

# Define the custom admin action for University
@admin.action(description="Delete ALL universities")
def delete_all_universities(modeladmin, request, queryset):
    University.objects.all().delete()
    modeladmin.message_user(request, "All universities have been deleted.")

# Create a custom admin class for University
@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon')
    actions = [delete_all_universities]

# Register Profile as before
admin.site.register(Profile)
