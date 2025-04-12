from django import forms
from .models import Project, Skill, MaxWordsValidator, ProjectApplication, RequiredRole, Language

class ProjectForm(forms.ModelForm):
    # Skills: Must be at least one (validation in clean_skills_required)
    skills_required = forms.CharField(widget=forms.HiddenInput(), required=True)
    # Required roles: Now set as required so that the user must select at least one.
    required_roles = forms.CharField(widget=forms.HiddenInput(), required=True)

    languages = forms.ModelMultipleChoiceField(
        queryset=Language.objects.all(),
        required=True,
        widget=forms.CheckboxSelectMultiple,  # Or use SelectMultiple for dropdown style
        help_text="Select at least one language"
    )

    class Meta:
        model = Project
        # Note: 'category' is handled via JavaScript.
        fields = [
            'title',
            'description',
            'skills_required',
            'is_active',
            'project_link',
            'project_mission',
            'project_objectives',
            'languages',
            'required_roles'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'project_mission': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Describe the mission of your project'
            }),
            'project_objectives': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Outline the objectives and scope'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If editing an existing project, prepopulate hidden fields with current values.
        if self.instance and self.instance.pk:
            skills = ",".join(str(skill.id) for skill in self.instance.skills_required.all())
            roles = ",".join(str(role.id) for role in self.instance.required_roles.all())
            self.fields['skills_required'].initial = skills
            self.fields['required_roles'].initial = roles
            print("DEBUG: ProjectForm __init__ - skills_required initial:", skills)
            print("DEBUG: ProjectForm __init__ - required_roles initial:", roles)

    def clean_languages(self):
        langs = self.cleaned_data.get('languages')
        if not langs:
            raise forms.ValidationError("Please select at least one language.")
        return langs

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if not title:
            raise forms.ValidationError("Project title is required.")
        if len(title) < 1:
            raise forms.ValidationError("Title must be at least 1 character long.")
        return title

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if not description:
            raise forms.ValidationError("Project description is required.")
        if len(description) < 1:
            raise forms.ValidationError("Description must be at least 1 characters long.")
        return description

    def clean_skills_required(self):
        data = self.cleaned_data.get('skills_required', '')
        if isinstance(data, list):
            skill_ids = data
        else:
            skill_ids = [id.strip() for id in data.split(',') if id.strip()]
        if not skill_ids:
            raise forms.ValidationError("At least one skill is required.")
        if len(skill_ids) > 15:
            raise forms.ValidationError("You can select at most 15 skills.")
        return skill_ids

    def clean_required_roles(self):
        roles_str = self.data.get('required_roles', '')
        role_ids = [rid.strip() for rid in roles_str.split(',') if rid.strip()]
        if not role_ids:
            raise forms.ValidationError("Please select at least one required role.")
        return role_ids

    def clean(self):
        cleaned_data = super().clean()
        # Process categories from the hidden input (IDs expected)
        categories_str = self.data.get('categories', '')
        category_ids = [cid.strip() for cid in categories_str.split(',') if cid.strip()]
        if not category_ids:
            raise forms.ValidationError("Please select at least one category.")
        if len(category_ids) > 5:
            raise forms.ValidationError("Select at most 5 categories.")
        cleaned_data['categories'] = category_ids
        return cleaned_data


class ProjectApplicationForm(forms.ModelForm):
    message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional message to the project owner'}),
        label="Message (optional)"
    )
    contribution = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe how you will contribute to the project'}),
        label="How will you contribute?",
        help_text="Please explain how your skills and experience will help the project."
    )
    applied_role = forms.ModelChoiceField(
        queryset=RequiredRole.objects.none(),  # Default to an empty QuerySet.
        required=True,
        label="Выберите роль, на которую вы подаетесь",
        widget=forms.Select(attrs={
            'class': 'w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )

    class Meta:
        model = ProjectApplication
        fields = ['applied_role', 'message', 'contribution']

    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        if project:
            self.fields['applied_role'].queryset = project.required_roles.all()


class ProjectDashboardForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            'title',
            'description',
            'project_mission',
            'project_objectives',
            'category',
            'skills_required',
            'languages',
            'required_roles',
            'view_count',
            'application_count',
            'is_active',
        ]
        widgets = {
            'category': forms.CheckboxSelectMultiple,
            'skills_required': forms.CheckboxSelectMultiple,
            'languages': forms.CheckboxSelectMultiple,
            'required_roles': forms.CheckboxSelectMultiple,
        }
