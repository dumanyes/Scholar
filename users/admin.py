from django.contrib import admin
from .models import Profile, University
from cities_light.models import Country

# Existing custom actions for other models...

# Define the custom admin action for University
@admin.action(description="Delete ALL universities")
def delete_all_universities(modeladmin, request, queryset):
    University.objects.all().delete()
    modeladmin.message_user(request, "All universities have been deleted.")

@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon')
    actions = [delete_all_universities]

# Register Profile as before
admin.site.register(Profile)
