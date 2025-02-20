from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.password_validation import validate_password

from .models import Profile, Interest, Skill, University
from cities_light.models import Country, City

import re
from django.core.exceptions import ValidationError

def validate_password_strength(value):
    """
    Validate that the password is at least 9 characters long,
    contains at least one uppercase letter and one symbol.
    """
    if len(value) < 9:
        raise ValidationError("Password must be at least 9 characters long.")
    if not re.search(r'[A-Z]', value):
        raise ValidationError("Password must contain at least one uppercase letter.")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
        raise ValidationError("Password must contain at least one special character.")


# In forms.py
class RegisterForm(UserCreationForm):
    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    username = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        validators=[validate_password, validate_password_strength]  # Add custom validator
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Explicitly remove password fields
        if 'password1' in self.fields:
            del self.fields['password1']
        if 'password2' in self.fields:
            del self.fields['password2']

    def clean_skills(self):
        skills = self.cleaned_data.get('skills')
        if len(skills) < 5:
            raise forms.ValidationError("Please select at least 5 skills.")
        return skills

    def clean_interests(self):
        interests = self.cleaned_data.get('interests')
        if len(interests) < 5:
            raise forms.ValidationError("Please select at least 5 interests.")
        return interests

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken. Please choose another one.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered. Please use another email or login.')
        return email

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Username', 'class': 'form-control'})
    )
    password = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-control'})
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = User
        fields = ['username', 'password']

    def confirm_login_allowed(self, user):
        """Override to apply remember_me functionality."""
        super().confirm_login_allowed(user)
        if self.cleaned_data.get('remember_me'):
            self.request.session.set_expiry(1209600)  # 2 weeks
        else:
            self.request.session.set_expiry(0)  # Session expires on browser close


class UpdateUserForm(forms.ModelForm):
    username = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['username', 'email']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise forms.ValidationError('This email is already in use.')
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.exclude(pk=self.instance.pk).filter(username=username).exists():
            raise forms.ValidationError('This username is already in use.')
        return username


class UpdateProfileForm(forms.ModelForm):
    avatar = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control-file'})
    )
    university = forms.ModelChoiceField(
        queryset=University.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5})
    )
    skills = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={'class': 'form-control'})
    )
    interests = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={'class': 'form-control'})
    )
    organization = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    position = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    linkedin = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={'class': 'form-control'})
    )
    github = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={'class': 'form-control'})
    )
    google_scholar = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={'class': 'form-control'})
    )
    telegram = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    country = forms.ModelChoiceField(
        queryset=Country.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    city = forms.ModelChoiceField(
        queryset=City.objects.none(),  # Initially empty, updated dynamically
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Profile
        fields = ['avatar', 'bio', 'organization', 'position', 'university', 'country', 'city', 'linkedin', 'github', 'google_scholar', 'telegram', 'skills', 'interests']

    def clean_skills(self):
        skill_names = self.cleaned_data.get('skills', '').split(',')
        skills = []
        for name in skill_names:
            name = name.strip()
            if name:
                skill, created = Skill.objects.get_or_create(
                    name=name,
                    defaults={'created_by': self.instance.user, 'approved': False}
                )
                skills.append(skill)
        return skills

    def clean_interests(self):
        interest_names = self.cleaned_data.get('interests', '').split(',')
        interests = []
        for name in interest_names:
            name = name.strip()
            if name:
                interest, created = Interest.objects.get_or_create(
                    name=name,
                    defaults={'created_by': self.instance.user, 'approved': False}
                )
                interests.append(interest)
        return interests

    def save(self, commit=True):
        profile = super().save(commit=commit)
        if commit:
            profile.skills.set(self.cleaned_data['skills'])
            profile.interests.set(self.cleaned_data['interests'])
        return profile
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.country:
            self.fields['city'].queryset = City.objects.filter(country=self.instance.country)
