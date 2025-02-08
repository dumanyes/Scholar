from django import forms
from django.contrib.auth.models import User

from .models import Project, Comment, Citation

from django import forms

from django import forms
from .models import Project, ResearchSection

class ResearchSectionForm(forms.ModelForm):
    class Meta:
        model = ResearchSection
        fields = ['title', 'content']

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'abstract', 'publish_date', 'pdf_file', 'citation', 'citation_link', 'tags']

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']

    content = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        label='Add a Comment',
    )


class CitationForm(forms.ModelForm):
    class Meta:
        model = Citation
        fields = ['author', 'title', 'journal_name', 'year', 'doi']

    author = forms.CharField(max_length=255)
    title = forms.CharField(max_length=255)
    journal_name = forms.CharField(max_length=255)
    year = forms.IntegerField(min_value=1000, max_value=9999)
    doi = forms.CharField(max_length=255, required=False)
