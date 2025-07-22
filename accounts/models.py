from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser
    """
    ROLE_CHOICES = [
        ('applicant', 'Applicant'),
        ('admin', 'Admin'),
        ('reviewer', 'Reviewer'),
        ('approver', 'Approver'),
    ]
    
    # Additional fields
    phone_number = PhoneNumberField(
        _('phone number'), 
        unique=True, 
        help_text=_('Enter phone number with country code e.g. +254712345678')
    )
    id_number = models.CharField(
        _('ID/Passport Number'), 
        max_length=20, 
        unique=True,
        help_text=_('Kenya National ID or Passport number')
    )
    role = models.CharField(
        _('role'), 
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='applicant'
    )
    is_verified = models.BooleanField(
        _('verified'), 
        default=False,
        help_text=_('Indicates if the user\'s phone number has been verified')
    )
    date_of_birth = models.DateField(_('date of birth'), null=True, blank=True)
    
    # Profile fields
    ward = models.CharField(_('ward'), max_length=100, blank=True)
    sub_county = models.CharField(_('sub-county'), max_length=100, blank=True)
    location = models.CharField(_('location'), max_length=100, blank=True)
    sub_location = models.CharField(_('sub-location'), max_length=100, blank=True)
    village = models.CharField(_('village'), max_length=100, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.username
    
    @property
    def is_applicant(self):
        return self.role == 'applicant'
    
    @property
    def is_admin(self):
        return self.role == 'admin' or self.is_superuser
    
    @property
    def is_reviewer(self):
        return self.role == 'reviewer'
    
    @property
    def is_approver(self):
        return self.role == 'approver'
    
    @property
    def can_review_applications(self):
        return self.role in ['admin', 'reviewer', 'approver'] or self.is_superuser
    
    @property
    def can_approve_applications(self):
        return self.role in ['admin', 'approver'] or self.is_superuser


class UserProfile(models.Model):
    """
    Extended profile information for users
    """
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile'
    )
    
    # Personal Information
    gender = models.CharField(
        _('gender'), 
        max_length=1, 
        choices=GENDER_CHOICES, 
        blank=True
    )
    guardian_name = models.CharField(
        _('guardian/parent name'), 
        max_length=200, 
        blank=True
    )
    guardian_phone = PhoneNumberField(
        _('guardian phone number'), 
        blank=True
    )
    guardian_relationship = models.CharField(
        _('relationship to guardian'), 
        max_length=50, 
        blank=True
    )
    
    # Emergency Contact
    emergency_contact_name = models.CharField(
        _('emergency contact name'), 
        max_length=200, 
        blank=True
    )
    emergency_contact_phone = PhoneNumberField(
        _('emergency contact phone'), 
        blank=True
    )
    
    # Additional Information
    special_needs = models.TextField(
        _('special needs/disabilities'), 
        blank=True,
        help_text=_('Describe any special needs or disabilities')
    )
    
    # Verification Documents
    id_card_front = models.ImageField(
        _('ID card front'), 
        upload_to='verification/id_cards/', 
        blank=True
    )
    id_card_back = models.ImageField(
        _('ID card back'), 
        upload_to='verification/id_cards/', 
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')
    
    def __str__(self):
        return f"Profile for {self.user.get_full_name()}"


class VerificationCode(models.Model):
    """
    Model to store verification codes for phone number verification
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='verification_codes'
    )
    code = models.CharField(_('verification code'), max_length=6)
    is_used = models.BooleanField(_('used'), default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'verification_codes'
        verbose_name = _('Verification Code')
        verbose_name_plural = _('Verification Codes')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Code for {self.user.phone_number}"
    
    @property
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at