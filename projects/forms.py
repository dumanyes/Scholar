from django import forms
from .models import Project, Skill, MaxWordsValidator, ProjectApplication, RequiredRole, Language, Category


class ProjectForm(forms.ModelForm):
    # —— New: explicit M2M field for categories ——
    category = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        required=True,
        widget=forms.CheckboxSelectMultiple,
        help_text="Select at least one category (max 5)"
    )

    # your JS will still populate these hidden inputs
    skills_required = forms.CharField(widget=forms.HiddenInput(), required=True)
    required_roles  = forms.CharField(widget=forms.HiddenInput(), required=True)

    languages = forms.ModelMultipleChoiceField(
        queryset=Language.objects.all(),
        required=True,
        widget=forms.CheckboxSelectMultiple,
        help_text="Select at least one language"
    )

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
            'project_link',
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
        if self.instance and self.instance.pk:
            # pre-fill hidden comma-lists for your JS
            self.fields['skills_required'].initial = ",".join(
                str(s.id) for s in self.instance.skills_required.all()
            )
            self.fields['required_roles'].initial = ",".join(
                str(r.id) for r in self.instance.required_roles.all()
            )
            # pre-check the existing categories
            self.fields['category'].initial = [
                c.id for c in self.instance.category.all()
            ]

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if not title:
            raise forms.ValidationError("Project title is required.")
        return title

    def clean_description(self):
        desc = self.cleaned_data.get('description', '').strip()
        if not desc:
            raise forms.ValidationError("Project description is required.")
        return desc

    def clean_languages(self):
        langs = self.cleaned_data.get('languages')
        if not langs:
            raise forms.ValidationError("Please select at least one language.")
        return langs

    def clean_category(self):
        cats = self.cleaned_data.get('category')
        if not cats:
            raise forms.ValidationError("Please select at least one category.")
        if len(cats) > 5:
            raise forms.ValidationError("Select at most 5 categories.")
        return cats

    def clean_skills_required(self):
        raw = self.data.getlist('skills_required')
        # Only allow numeric ids
        skill_ids = []
        for sid in raw:
            sid = sid.strip()
            if not sid:
                continue
            if not sid.isdigit():
                raise forms.ValidationError(f"Invalid skill ID: {sid}")
            skill_ids.append(int(sid))

        if not skill_ids:
            raise forms.ValidationError("At least one skill is required.")
        if len(skill_ids) > 15:
            raise forms.ValidationError("You can select at most 15 skills.")
        return skill_ids

    def clean_required_roles(self):
        role_ids = [rid for rid in self.data.getlist('required_roles') if rid.strip()]
        if not role_ids:
            raise forms.ValidationError("Please select at least one required role.")
        return role_ids


from django import forms
from .models import ProjectApplication, RequiredRole

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
        queryset=RequiredRole.objects.none(),
        required=True,
        label="Select the role you're applying for",
        widget=forms.Select(attrs={
            'class': 'w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
        })
    )


    class Meta:
        model = ProjectApplication
        fields = ['applied_role', 'message', 'contribution', 'resume', 'resume_link']  # Not including resume/resume_link here

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
