from datetime import date

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
import re
from .models import Profile, University
from projects.models import Skill, Interest

def validate_username(value):
    if len(value) < 3:
        raise ValidationError("Username must be at least 3 characters long.")
    if not re.match(r'^\w+$', value):  # Letters, numbers, underscores
        raise ValidationError("Username can only contain letters, numbers, and underscores.")
    if User.objects.filter(username=value).exists():
        raise ValidationError("This username is already taken.")

def validate_password_strength(value):
    if len(value) < 8:
        raise ValidationError("Password must be at least 8 characters long.")
    if not re.search(r'[A-Z]', value):
        raise ValidationError("Password must contain at least one uppercase letter.")
    if not re.search(r'[a-z]', value):
        raise ValidationError("Password must contain at least one lowercase letter.")
    if not re.search(r'\d', value):
        raise ValidationError("Password must contain at least one number.")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>+_-]', value):
        raise ValidationError("Password must contain at least one special character.")

class RegisterForm(UserCreationForm):
    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        error_messages={'required': "This field is required."}
    )
    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        error_messages={'required': "This field is required."}
    )
    username = forms.CharField(
        required=True,
        validators=[validate_username],
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        error_messages={'required': "Username is required."}
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        error_messages={'required': "Email is required.", 'invalid': "Please enter a valid email address."}
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        validators=[validate_password_strength],
        error_messages={'required': "Password is required."}
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        error_messages={'required': "Password confirmation is required."}
    )
    birthdate = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        error_messages={'invalid': "Please enter a valid date."}
    )
    terms_and_conditions = forms.BooleanField(
        required=True,
        error_messages={'required': "You must agree to the terms and conditions to continue."}
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'password1', 'password2', 'birthdate', 'terms_and_conditions')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        return email

    def clean_birthdate(self):
        birthdate = self.cleaned_data.get('birthdate')
        if birthdate:
            today = date.today()
            age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
            if age < 13:
                raise ValidationError('You must be at least 13 years old to register.')
        return birthdate

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords do not match.")
        return password2

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
        super().confirm_login_allowed(user)
        if self.cleaned_data.get('remember_me'):
            self.request.session.set_expiry(1209600)  # 2 weeks
        else:
            self.request.session.set_expiry(0)  # Session expires on browser close

from django import forms
from django.contrib.auth.models import User
from .models import Profile, University
from projects.models import Skill, Category

class UpdateUserForm(forms.ModelForm):
    username = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'email']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # If the email wasn't changed, simply return it.
        if self.instance and self.instance.email.lower() == email.lower():
            return email

        # Otherwise, check if the new email is already in use.
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('This email is already in use.')
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.exclude(pk=self.instance.pk).filter(username=username).exists():
            raise forms.ValidationError('This username is already in use.')
        return username

class UpdateProfileForm(forms.ModelForm):
    avatar = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control-file'}))
    university = forms.ModelChoiceField(queryset=University.objects.all(), required=False,
                                        widget=forms.Select(attrs={'class': 'form-control'}))
    bio = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5}))
    # Remove interests field.
    # Add hidden fields for skills and categories.
    skills = forms.CharField(required=False, widget=forms.HiddenInput(attrs={'class': 'form-control'}))
    categories = forms.CharField(required=False, widget=forms.HiddenInput(attrs={'class': 'form-control'}))
    organization = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    position = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    linkedin = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-control'}))
    github = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-control'}))
    google_scholar = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-control'}))
    telegram = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Profile
        fields = [
            'avatar', 'bio', 'organization', 'position', 'university', 'linkedin',
            'github', 'google_scholar', 'telegram', 'skills', 'categories'
        ]

    def clean_skills(self):
        skills_str = self.cleaned_data.get('skills', '')
        try:
            skill_ids = [int(s) for s in skills_str.split(",") if s]
        except ValueError:
            raise forms.ValidationError("Invalid skills data.")
        from projects.models import Skill
        skills = Skill.objects.filter(id__in=skill_ids)
        if not skills.exists():
            raise forms.ValidationError("Please select at least one valid skill.")
        return skills

    def clean_categories(self):
        # Remove max count validation for categories.
        categories_str = self.cleaned_data.get('categories', '')
        try:
            category_ids = [int(c) for c in categories_str.split(",") if c]
        except ValueError:
            raise forms.ValidationError("Invalid categories data.")
        from projects.models import Category
        categories = Category.objects.filter(id__in=category_ids)
        if not categories.exists():
            raise forms.ValidationError("Please select at least one category.")
        return categories

    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            profile.save()
            profile.skills.set(self.cleaned_data['skills'])
            # Save the categories to the new ManyToMany field:
            profile.categories.set(self.cleaned_data['categories'])
        return profile

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        initial = kwargs.get('initial', {})
        if instance:
            initial['skills'] = ",".join(str(skill.id) for skill in instance.skills.all())
            initial['categories'] = ",".join(str(cat.id) for cat in instance.categories.all())
            kwargs['initial'] = initial

        super().__init__(*args, **kwargs)



class UserDashboardForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'is_staff', 'is_active']

class ProfileDashboardForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'bio', 'birthdate', 'university', 'skills', 'categories',
            'organization', 'position', 'linkedin', 'github',
            'google_scholar', 'telegram', 'country', 'city',
            'reputation', 'is_verified'
        ]
        widgets = {
            'skills': forms.CheckboxSelectMultiple,
            'categories': forms.CheckboxSelectMultiple,
        }


