from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.db.models import Sum, Count
from django.utils.translation import gettext_lazy as _
from .models import (
    AcademicYear, Institution, BursaryApplication, 
    ApplicationDocument, ApplicationStatusLog, Disbursement
)


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    """Admin for academic years"""
    list_display = ('year', 'start_date', 'end_date', 'application_deadline', 'is_active')
    list_filter = ('is_active', 'start_date')
    search_fields = ('year',)
    ordering = ('-start_date',)
    
    fieldsets = (
        (None, {
            'fields': ('year', 'is_active')
        }),
        ('Important Dates', {
            'fields': ('start_date', 'end_date', 'application_deadline')
        }),
    )


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    """Admin for institutions"""
    list_display = ('name', 'institution_type', 'county', 'is_verified')
    list_filter = ('institution_type', 'county', 'is_verified')
    search_fields = ('name', 'county')
    ordering = ('name',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'institution_type', 'is_verified')
        }),
        ('Location', {
            'fields': ('county', 'address')
        }),
    )
    
    actions = ['verify_institutions']
    
    def verify_institutions(self, request, queryset):
        count = queryset.update(is_verified=True)
        self.message_user(request, f'{count} institutions verified.')
    verify_institutions.short_description = 'Verify selected institutions'


class ApplicationDocumentInline(admin.TabularInline):
    """Inline admin for application documents"""
    model = ApplicationDocument
    extra = 0
    readonly_fields = ('uploaded_at', 'file_size_display')
    fields = ('document_type', 'description', 'file', 'file_size_display', 'uploaded_at')
    
    def file_size_display(self, obj):
        if obj.file:
            size = obj.file.size
            if size < 1024:
                return f'{size} bytes'
            elif size < 1024 * 1024:
                return f'{size / 1024:.1f} KB'
            else:
                return f'{size / (1024 * 1024):.1f} MB'
        return '-'
    file_size_display.short_description = 'File Size'


class ApplicationStatusLogInline(admin.TabularInline):
    """Inline admin for status logs"""
    model = ApplicationStatusLog
    extra = 0
    readonly_fields = ('created_at', 'changed_by')
    fields = ('previous_status', 'new_status', 'changed_by', 'comment', 'created_at')
    ordering = ('-created_at',)


@admin.register(BursaryApplication)
class BursaryApplicationAdmin(admin.ModelAdmin):
    """Admin for bursary applications"""
    list_display = ('application_number', 'applicant_name', 'education_level', 
                   'amount_requested', 'status', 'submitted_at', 'academic_year')
    list_filter = ('status', 'education_level', 'academic_year', 'is_orphan', 
                  'is_single_parent', 'has_disability', 'submitted_at')
    search_fields = ('application_number', 'applicant__first_name', 
                    'applicant__last_name', 'applicant__id_number')
    readonly_fields = ('application_number', 'created_at', 'updated_at', 
                      'submitted_at', 'reviewed_at', 'approved_at')
    inlines = [ApplicationDocumentInline, ApplicationStatusLogInline]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Application Information', {
            'fields': ('application_number', 'applicant', 'academic_year', 'status')
        }),
        ('Educational Information', {
            'fields': ('education_level', 'institution', 'institution_name_other',
                      'admission_number', 'course_name', 'year_of_study')
        }),
        ('Financial Information', {
            'fields': ('total_fees', 'amount_requested', 'other_support', 
                      'approved_amount', 'family_monthly_income')
        }),
        ('Family Background', {
            'fields': ('number_of_siblings', 'siblings_in_school', 'is_orphan',
                      'is_single_parent', 'has_disability')
        }),
        ('Special Circumstances', {
            'fields': ('special_circumstances',),
            'classes': ('collapse',)
        }),
        ('Review Information', {
            'fields': ('reviewed_by', 'reviewed_at', 'reviewer_comments',
                      'approved_by', 'approved_at', 'rejection_reason'),
            'classes': ('collapse',)
        }),
        ('Internal Notes', {
            'fields': ('internal_notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'submitted_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_under_review', 'export_as_csv']
    
    def applicant_name(self, obj):
        return obj.applicant.get_full_name()
    applicant_name.short_description = 'Applicant'
    applicant_name.admin_order_field = 'applicant__first_name'
    
    def mark_as_under_review(self, request, queryset):
        count = queryset.filter(status='submitted').update(status='under_review')
        self.message_user(request, f'{count} applications marked as under review.')
    mark_as_under_review.short_description = 'Mark as under review'
    
    def export_as_csv(self, request, queryset):
        # This would implement CSV export functionality
        pass
    export_as_csv.short_description = 'Export selected as CSV'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('applicant', 'academic_year', 'institution')


@admin.register(Disbursement)
class DisbursementAdmin(admin.ModelAdmin):
    """Admin for disbursements"""
    list_display = ('reference_number', 'application_link', 'amount', 
                   'payment_method', 'payment_date', 'processed_by')
    list_filter = ('payment_method', 'payment_date')
    search_fields = ('reference_number', 'application__application_number', 
                    'paid_to', 'receipt_number')
    date_hierarchy = 'payment_date'
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Disbursement Information', {
            'fields': ('application', 'amount', 'payment_method', 'reference_number')
        }),
        ('Payment Details', {
            'fields': ('paid_to', 'payment_date', 'receipt_number', 'processed_by')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_at')
        }),
    )
    
    def application_link(self, obj):
        url = reverse('admin:bursary_bursaryapplication_change', args=[obj.application.pk])
        return format_html('<a href="{}">{}</a>', url, obj.application.application_number)
    application_link.short_description = 'Application'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('application', 'processed_by')


# Register admin actions
def get_application_summary(modeladmin, request, queryset):
    """Generate summary statistics for selected applications"""
    total = queryset.count()
    total_requested = queryset.aggregate(Sum('amount_requested'))['amount_requested__sum'] or 0
    total_approved = queryset.filter(status='approved').aggregate(
        Sum('approved_amount'))['approved_amount__sum'] or 0
    
    by_status = queryset.values('status').annotate(count=Count('id'))
    by_education = queryset.values('education_level').annotate(count=Count('id'))
    
    # This would generate a detailed report
    pass

get_application_summary.short_description = "Generate summary report"