# projects/forms.py
from django import forms
from .models import Project

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'category', 'skills_required', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }