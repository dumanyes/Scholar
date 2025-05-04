from django.contrib import admin
from .models import (
    Project,
    Category,
    Skill,
    InterestsCategory,
    InterestsSubCategory,
    Interest,
    Language,
    RequiredRole,
    ProjectApplication
)

@admin.action(description="Activate selected projects")
def activate_projects(modeladmin, request, queryset):
    updated = queryset.update(is_active=True)
    modeladmin.message_user(request, f"{updated} project(s) activated.")

@admin.action(description="Deactivate selected projects")
def deactivate_projects(modeladmin, request, queryset):
    updated = queryset.update(is_active=False)
    modeladmin.message_user(request, f"{updated} project(s) deactivated.")

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'description')
    actions = [activate_projects, deactivate_projects]

# Register other models
admin.site.register(Category)
admin.site.register(InterestsCategory)
admin.site.register(InterestsSubCategory)
admin.site.register(Language)
admin.site.register(RequiredRole)
admin.site.register(ProjectApplication)

# Skill admin with delete-all action
@admin.action(description="Delete ALL skills")
def delete_all_skills(modeladmin, request, queryset):
    Skill.objects.all().delete()
    modeladmin.message_user(request, "All skills have been deleted.")

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    actions = [delete_all_skills]

# Interest admin with delete-all action
@admin.action(description="Delete ALL interests")
def delete_all_interests(modeladmin, request, queryset):
    Interest.objects.all().delete()
    modeladmin.message_user(request, "All interests have been deleted.")

@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_subcategory',)
    search_fields = ('name',)
    list_filter = ('subcategory__category', 'subcategory',)
    actions = [delete_all_interests]

    def display_subcategory(self, obj):
        return f"{obj.subcategory.name} ({obj.subcategory.category.name})"
    display_subcategory.short_description = "Subcategory (Category)"
