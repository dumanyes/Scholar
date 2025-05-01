from django.contrib import admin
from .models import Profile, University
@admin.action(description="Delete ALL universities")
def delete_all_universities(modeladmin, request, queryset):
    University.objects.all().delete()
    modeladmin.message_user(request, "All universities have been deleted.")

@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon')
    actions = [delete_all_universities]

admin.site.register(Profile)
