from django import forms
from .models import Project

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        # Note: We removed 'category' from fields because you're handling categories via JavaScript.
        fields = ['title', 'description', 'skills_required', 'is_active',
                  'project_mission', 'project_objectives', 'languages', 'required_roles']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'project_mission': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Describe the mission of your project'}),
            'project_objectives': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Outline the objectives and scope'}),
        }

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if not title:
            raise forms.ValidationError("Project title is required.")
        if len(title) < 5:
            raise forms.ValidationError("Title must be at least 5 characters long.")
        return title

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if not description:
            raise forms.ValidationError("Project description is required.")
        if len(description) < 20:
            raise forms.ValidationError("Description must be at least 20 characters long.")
        return description

    def clean_skills_required(self):
        skills = self.cleaned_data.get('skills_required')
        if not skills:
            raise forms.ValidationError("At least one skill is required.")
        skills_list = [skill.strip() for skill in skills.split(',') if skill.strip()]
        if not skills_list:
            raise forms.ValidationError("At least one skill is required.")
        if len(skills_list) > 10:
            raise forms.ValidationError("You can select at most 10 skills.")
        return ', '.join(skills_list)

    def clean(self):
        cleaned_data = super().clean()
        # Process categories from the hidden input (handled by JS)
        categories_str = self.data.get('categories', '')
        category_list = [cat.strip() for cat in categories_str.split(',') if cat.strip()]
        if not category_list:
            raise forms.ValidationError("Please select at least one category.")
        if len(category_list) > 5:
            raise forms.ValidationError("Select at most 5 categories.")
        cleaned_data['categories'] = category_list
        return cleaned_data
