from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserProfile, VerificationCode


class UserProfileInline(admin.StackedInline):
    """Inline admin for user profiles"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('gender', 'guardian_name', 'guardian_phone', 'guardian_relationship')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone')
        }),
        ('Additional Information', {
            'fields': ('special_needs',)
        }),
        ('Verification Documents', {
            'fields': ('id_card_front', 'id_card_back'),
            'classes': ('collapse',)
        }),
    )


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom admin for User model"""
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'phone_number', 
                   'role', 'is_verified', 'is_active', 'date_joined')
    list_filter = ('role', 'is_verified', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone_number', 'id_number')
    ordering = ('-date_joined',)
    
    fieldsets = UserAdmin.fieldsets + (
        (_('Additional Information'), {
            'fields': ('phone_number', 'id_number', 'role', 'is_verified', 'date_of_birth')
        }),
        (_('Location Information'), {
            'fields': ('ward', 'sub_county', 'location', 'sub_location', 'village'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        (_('Additional Information'), {
            'fields': ('email', 'phone_number', 'id_number', 'role', 'date_of_birth',
                      'first_name', 'last_name')
        }),
        (_('Location Information'), {
            'fields': ('ward', 'sub_county', 'location', 'sub_location', 'village')
        }),
    )
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)


@admin.register(VerificationCode)
class VerificationCodeAdmin(admin.ModelAdmin):
    """Admin for verification codes"""
    list_display = ('user', 'code', 'is_used', 'created_at', 'expires_at', 'is_expired')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__username', 'user__phone_number', 'code')
    readonly_fields = ('code', 'created_at', 'expires_at')
    
    def is_expired(self, obj):
        return obj.is_expired
    is_expired.boolean = True
    is_expired.short_description = 'Expired'
    
    def has_add_permission(self, request):
        # Prevent manual creation of verification codes
        return False


# Customize admin site
admin.site.site_header = "Constituency Bursary Management System"
admin.site.site_title = "Bursary Admin"
admin.site.index_title = "Welcome to Bursary Administration"