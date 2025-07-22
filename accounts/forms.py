from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from phonenumber_field.formfields import PhoneNumberField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, Div, HTML
from .models import User, UserProfile
import re


class CustomAuthenticationForm(AuthenticationForm):
    """
    Custom login form with phone number or username support
    """
    username = forms.CharField(
        label=_("Username or Phone Number"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username or phone number',
            'autocomplete': 'username'
        })
    )
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password',
            'autocomplete': 'current-password'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('username', css_class='mb-3'),
            Field('password', css_class='mb-3'),
            Submit('submit', 'Login', css_class='btn btn-primary btn-block')
        )
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Check if it's a phone number
        if username.startswith('+') or username.isdigit():
            # Try to find user by phone number
            try:
                user = User.objects.get(phone_number=username)
                return user.username
            except User.DoesNotExist:
                pass
        return username


class UserRegistrationForm(UserCreationForm):
    """
    Registration form for new users
    """
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter first name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter last name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email address'
        })
    )
    phone_number = PhoneNumberField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+254712345678'
        }),
        help_text=_('Enter phone number with country code')
    )
    id_number = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter ID/Passport number'
        }),
        help_text=_('Kenya National ID or Passport number')
    )
    date_of_birth = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    # Address fields
    ward = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter ward'
        })
    )
    location = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter location'
        })
    )
    sub_location = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter sub-location'
        })
    )
    village = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter village'
        })
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email', 
            'phone_number', 'id_number', 'date_of_birth',
            'password1', 'password2', 'ward', 'location', 
            'sub_location', 'village'
        ]
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choose a username'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            HTML('<h4 class="mb-3">Personal Information</h4>'),
            Row(
                Column('first_name', css_class='col-md-6'),
                Column('last_name', css_class='col-md-6'),
                css_class='mb-3'
            ),
            Row(
                Column('username', css_class='col-md-6'),
                Column('email', css_class='col-md-6'),
                css_class='mb-3'
            ),
            Row(
                Column('phone_number', css_class='col-md-6'),
                Column('id_number', css_class='col-md-6'),
                css_class='mb-3'
            ),
            Field('date_of_birth', css_class='mb-3'),
            
            HTML('<h4 class="mb-3 mt-4">Location Information</h4>'),
            Row(
                Column('ward', css_class='col-md-6'),
                Column('location', css_class='col-md-6'),
                css_class='mb-3'
            ),
            Row(
                Column('sub_location', css_class='col-md-6'),
                Column('village', css_class='col-md-6'),
                css_class='mb-3'
            ),
            
            HTML('<h4 class="mb-3 mt-4">Security Information</h4>'),
            Field('password1', css_class='mb-3'),
            Field('password2', css_class='mb-3'),
            
            Submit('submit', 'Register', css_class='btn btn-primary btn-lg btn-block')
        )
    
    def clean_id_number(self):
        id_number = self.cleaned_data.get('id_number')
        # Basic validation for Kenyan ID (8 digits) or passport
        if id_number.isdigit() and len(id_number) != 8:
            raise ValidationError(_('Kenya National ID must be 8 digits'))
        return id_number
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError(_('This email is already registered'))
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            # Create user profile
            UserProfile.objects.create(user=user)
        return user


class UserProfileForm(forms.ModelForm):
    """
    Form for updating user profile information
    """
    class Meta:
        model = UserProfile
        fields = [
            'gender', 'guardian_name', 'guardian_phone',
            'guardian_relationship', 'emergency_contact_name',
            'emergency_contact_phone', 'special_needs',
            'id_card_front', 'id_card_back'
        ]
        widgets = {
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'guardian_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Guardian/Parent full name'
            }),
            'guardian_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+254712345678'
            }),
            'guardian_relationship': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Father, Mother, Uncle'
            }),
            'emergency_contact_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Emergency contact full name'
            }),
            'emergency_contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+254712345678'
            }),
            'special_needs': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe any special needs or disabilities'
            }),
            'id_card_front': forms.FileInput(attrs={'class': 'form-control'}),
            'id_card_back': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.layout = Layout(
            HTML('<h4 class="mb-3">Additional Information</h4>'),
            Field('gender', css_class='mb-3'),
            
            HTML('<h4 class="mb-3 mt-4">Guardian Information</h4>'),
            Row(
                Column('guardian_name', css_class='col-md-4'),
                Column('guardian_phone', css_class='col-md-4'),
                Column('guardian_relationship', css_class='col-md-4'),
                css_class='mb-3'
            ),
            
            HTML('<h4 class="mb-3 mt-4">Emergency Contact</h4>'),
            Row(
                Column('emergency_contact_name', css_class='col-md-6'),
                Column('emergency_contact_phone', css_class='col-md-6'),
                css_class='mb-3'
            ),
            
            Field('special_needs', css_class='mb-3'),
            
            HTML('<h4 class="mb-3 mt-4">Verification Documents</h4>'),
            Row(
                Column('id_card_front', css_class='col-md-6'),
                Column('id_card_back', css_class='col-md-6'),
                css_class='mb-3'
            ),
            
            Submit('submit', 'Update Profile', css_class='btn btn-primary')
        )


class EmailVerificationForm(forms.Form):
    """
    Form for email address verification
    """
    verification_code = forms.CharField(
        max_length=6,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'placeholder': '000000',
            'maxlength': '6',
            'pattern': '[0-9]{6}'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('verification_code'),
            Submit('submit', 'Verify', css_class='btn btn-primary btn-block mt-3')
        )