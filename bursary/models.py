from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import uuid
import os

class AcademicYear(models.Model):
    """
    Model to manage academic years for bursary applications
    """
    year = models.CharField(
        _('academic year'), 
        max_length=20, 
        unique=True,
        help_text=_('e.g., 2024/2025')
    )
    start_date = models.DateField(_('start date'))
    end_date = models.DateField(_('end date'))
    is_active = models.BooleanField(_('active'), default=True)
    application_deadline = models.DateTimeField(_('application deadline'))
    
    class Meta:
        db_table = 'academic_years'
        verbose_name = _('Academic Year')
        verbose_name_plural = _('Academic Years')
        ordering = ['-start_date']
    
    def __str__(self):
        return self.year


class Institution(models.Model):
    """
    Model for educational institutions
    """
    INSTITUTION_TYPES = [
        ('primary', 'Primary School'),
        ('secondary', 'Secondary School'),
        ('tvet', 'TVET/Technical College'),
        ('university', 'University'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(_('institution name'), max_length=200)
    institution_type = models.CharField(
        _('type'), 
        max_length=20, 
        choices=INSTITUTION_TYPES
    )
    county = models.CharField(_('county'), max_length=100)
    address = models.TextField(_('address'))
    is_verified = models.BooleanField(_('verified'), default=False)
    
    class Meta:
        db_table = 'institutions'
        verbose_name = _('Institution')
        verbose_name_plural = _('Institutions')
        ordering = ['name']
        unique_together = ['name', 'county']
    
    def __str__(self):
        return f"{self.name} ({self.get_institution_type_display()})"


class BursaryApplication(models.Model):
    """
    Main model for bursary applications
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('verified', 'Verified'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('disbursed', 'Disbursed'),
    ]
    
    EDUCATION_LEVEL_CHOICES = [
        ('primary', 'Primary School'),
        ('secondary', 'Secondary School'),
        ('tvet', 'TVET/Technical College'),
        ('undergraduate', 'Undergraduate'),
        ('postgraduate', 'Postgraduate'),
    ]
    
    # Unique identifier
    application_number = models.CharField(
        _('application number'), 
        max_length=20, 
        unique=True, 
        editable=False
    )
    
    # Applicant information
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='applications'
    )
    academic_year = models.ForeignKey(
        AcademicYear, 
        on_delete=models.PROTECT, 
        related_name='applications'
    )
    
    # Educational information
    education_level = models.CharField(
        _('education level'), 
        max_length=20, 
        choices=EDUCATION_LEVEL_CHOICES
    )
    institution = models.ForeignKey(
        Institution, 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True,
        related_name='applications'
    )
    institution_name_other = models.CharField(
        _('institution name (if not listed)'), 
        max_length=200, 
        blank=True
    )
    admission_number = models.CharField(
        _('admission/registration number'), 
        max_length=50
    )
    course_name = models.CharField(
        _('course/class name'), 
        max_length=200,
        help_text=_('e.g., Form 2, Bachelor of Science in Computer Science')
    )
    year_of_study = models.IntegerField(
        _('year/form of study'),
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    
    # Financial information
    total_fees = models.DecimalField(
        _('total fees required'), 
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    amount_requested = models.DecimalField(
        _('amount requested'), 
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    other_support = models.DecimalField(
        _('other financial support received'), 
        max_digits=10, 
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    # Family information
    family_monthly_income = models.DecimalField(
        _('family monthly income'), 
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    number_of_siblings = models.IntegerField(
        _('number of siblings'), 
        default=0,
        validators=[MinValueValidator(0)]
    )
    siblings_in_school = models.IntegerField(
        _('siblings in school'), 
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    # Special circumstances
    is_orphan = models.BooleanField(_('orphan'), default=False)
    is_single_parent = models.BooleanField(_('single parent family'), default=False)
    has_disability = models.BooleanField(_('has disability'), default=False)
    special_circumstances = models.TextField(
        _('special circumstances'), 
        blank=True,
        help_text=_('Describe any special circumstances affecting your need for bursary')
    )

    # =====================================================================
    # EXTENDED FIELDS (NG-CDF Bursary Application Standard)
    # =====================================================================

    # --- Extended Institutional Details ---
    MODE_OF_STUDY_CHOICES = [
        ('regular', 'Regular'),
        ('parallel', 'Parallel'),
        ('boarding', 'Boarding'),
        ('day', 'Day Scholar'),
    ]
    campus_branch = models.CharField(_('campus/branch'), max_length=200, blank=True,
        help_text=_('For tertiary institutions and universities'))
    faculty_department = models.CharField(_('faculty/department'), max_length=200, blank=True,
        help_text=_('For tertiary institutions and universities'))
    mode_of_study = models.CharField(_('mode of study'), max_length=20,
        choices=MODE_OF_STUDY_CHOICES, blank=True)
    course_duration = models.IntegerField(_('course duration (years)'), null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)])
    expected_completion = models.CharField(_('expected completion (MM/YYYY)'), max_length=10, blank=True)

    # --- Family Status ---
    FAMILY_STATUS_CHOICES = [
        ('both_alive', 'Both Parents Alive'),
        ('one_dead', 'One Parent Dead'),
        ('both_dead', 'Both Parents Dead'),
        ('single_parent', 'Single Parent'),
        ('other', 'Other'),
    ]
    family_status = models.CharField(_('family status'), max_length=20,
        choices=FAMILY_STATUS_CHOICES, blank=True)
    family_status_other = models.CharField(_('other family status (specify)'), max_length=200, blank=True)
    family_annual_income = models.DecimalField(_('estimated annual family income (KES)'),
        max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    family_annual_expenses = models.DecimalField(_('estimated annual family expenses (KES)'),
        max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])

    # --- Father's Details ---
    EMPLOYMENT_TYPE_CHOICES = [
        ('permanent', 'Permanent'),
        ('contractual', 'Contractual'),
        ('casual', 'Casual'),
        ('retired', 'Retired'),
        ('self_employed', 'Self Employed'),
        ('none', 'None / Unemployed'),
    ]
    father_name = models.CharField(_("father's full name"), max_length=200, blank=True)
    father_address = models.CharField(_("father's address"), max_length=200, blank=True)
    father_telephone = models.CharField(_("father's telephone"), max_length=20, blank=True)
    father_occupation = models.CharField(_("father's occupation"), max_length=200, blank=True)
    father_employment_type = models.CharField(_("father's employment type"), max_length=20,
        choices=EMPLOYMENT_TYPE_CHOICES, blank=True)
    father_income_source = models.CharField(_("father's main source of income"), max_length=200, blank=True)

    # --- Mother's Details ---
    mother_name = models.CharField(_("mother's full name"), max_length=200, blank=True)
    mother_address = models.CharField(_("mother's address"), max_length=200, blank=True)
    mother_telephone = models.CharField(_("mother's telephone"), max_length=20, blank=True)
    mother_occupation = models.CharField(_("mother's occupation"), max_length=200, blank=True)
    mother_employment_type = models.CharField(_("mother's employment type"), max_length=20,
        choices=EMPLOYMENT_TYPE_CHOICES, blank=True)
    mother_income_source = models.CharField(_("mother's main source of income"), max_length=200, blank=True)

    # --- Guardian Details (on the application, separate from user profile) ---
    app_guardian_name = models.CharField(_("guardian's full name"), max_length=200, blank=True)
    app_guardian_address = models.CharField(_("guardian's address"), max_length=200, blank=True)
    app_guardian_telephone = models.CharField(_("guardian's telephone"), max_length=20, blank=True)
    app_guardian_occupation = models.CharField(_("guardian's occupation"), max_length=200, blank=True)
    app_guardian_employment_type = models.CharField(_("guardian's employment type"), max_length=20,
        choices=EMPLOYMENT_TYPE_CHOICES, blank=True)
    app_guardian_income_source = models.CharField(_("guardian's main source of income"), max_length=200, blank=True)

    # --- Applicant's Additional Information ---
    reason_for_applying = models.TextField(_('why are you applying for bursary assistance?'), blank=True)
    previous_cdf_support = models.BooleanField(
        _('received NG-CDF bursary in the past?'), default=False)
    previous_cdf_support_details = models.TextField(
        _('if yes, specify amount and when'), blank=True)
    previous_other_support_received = models.BooleanField(
        _('received bursary from other organizations?'), default=False)
    previous_other_support_details = models.TextField(
        _('if yes, provide details'), blank=True)
    disability_details = models.TextField(
        _('disability details'), blank=True,
        help_text=_('If you have a disability, provide details'))
    has_chronic_illness = models.BooleanField(_('has chronic illness'), default=False)
    chronic_illness_details = models.TextField(_('chronic illness details'), blank=True)
    parent_has_disability = models.BooleanField(
        _('parent/guardian has disability'), default=False)
    parent_disability_details = models.TextField(
        _('parent/guardian disability details'), blank=True)
    parent_has_chronic_illness = models.BooleanField(
        _('parent/guardian has chronic illness'), default=False)
    parent_chronic_illness_details = models.TextField(
        _('parent/guardian chronic illness details'), blank=True)

    # --- Academic Performance ---
    ACADEMIC_PERFORMANCE_CHOICES = [
        ('excellent', 'Excellent'),
        ('very_good', 'Very Good'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
    ]
    academic_performance = models.CharField(_('average academic performance'), max_length=20,
        choices=ACADEMIC_PERFORMANCE_CHOICES, blank=True)
    been_sent_away = models.BooleanField(
        _('have you been sent away from school?'), default=False)
    sent_away_reasons = models.TextField(_('reasons for absence'), blank=True)
    sent_away_weeks = models.IntegerField(_('weeks away from school'), null=True, blank=True,
        validators=[MinValueValidator(0)])
    annual_fees_per_structure = models.DecimalField(
        _('annual fees as per fee structure (KES)'),
        max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    last_term_balance = models.DecimalField(
        _("last semester/term's fee balance (KES)"),
        max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    current_term_balance = models.DecimalField(
        _("this semester/term's fee balance (KES)"),
        max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    next_term_balance = models.DecimalField(
        _("next semester/term's fee balance (KES)"),
        max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    helb_loan_amount = models.DecimalField(
        _('HELB loan amount (where applicable)'),
        max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])

    # --- Education Funding History ---
    funding_source_secondary = models.CharField(
        _('main funding source (secondary)'), max_length=200, blank=True)
    funding_source_college = models.CharField(
        _('main funding source (college)'), max_length=200, blank=True)
    funding_source_university = models.CharField(
        _('main funding source (university)'), max_length=200, blank=True)
    other_funding_secondary = models.CharField(
        _('other funding (secondary)'), max_length=200, blank=True)
    other_funding_college = models.CharField(
        _('other funding (college)'), max_length=200, blank=True)
    other_funding_university = models.CharField(
        _('other funding (university)'), max_length=200, blank=True)

    # --- Referees ---
    referee1_name = models.CharField(_('referee 1 name'), max_length=200, blank=True)
    referee1_address = models.CharField(_('referee 1 address'), max_length=200, blank=True)
    referee1_telephone = models.CharField(_('referee 1 telephone'), max_length=20, blank=True)
    referee2_name = models.CharField(_('referee 2 name'), max_length=200, blank=True)
    referee2_address = models.CharField(_('referee 2 address'), max_length=200, blank=True)
    referee2_telephone = models.CharField(_('referee 2 telephone'), max_length=20, blank=True)

    # --- Declarations ---
    student_declaration_accepted = models.BooleanField(
        _("student's declaration accepted"), default=False,
        help_text=_('Student confirms all information is true and accurate'))
    guardian_declaration_accepted = models.BooleanField(
        _("parent/guardian declaration accepted"), default=False,
        help_text=_('Student confirms on behalf of parent/guardian'))
    declaration_accepted_at = models.DateTimeField(
        _('declaration accepted at'), null=True, blank=True)

    # --- Optional Signature Uploads ---
    student_signature = models.ImageField(
        _("student's signature"),
        upload_to='signatures/students/',
        blank=True,
        help_text=_('Upload an image of your signature (optional, for printed form)'))
    guardian_signature = models.ImageField(
        _("parent/guardian's signature"),
        upload_to='signatures/guardians/',
        blank=True,
        help_text=_('Upload an image of parent/guardian signature (optional)'))

    # Status and tracking
    status = models.CharField(
        _('status'), 
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='draft'
    )
    submitted_at = models.DateTimeField(_('submitted at'), null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reviewed_applications'
    )
    reviewed_at = models.DateTimeField(_('reviewed at'), null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_applications'
    )
    approved_at = models.DateTimeField(_('approved at'), null=True, blank=True)
    approved_amount = models.DecimalField(
        _('approved amount'), 
        max_digits=10, 
        decimal_places=2,
        null=True, 
        blank=True,
        validators=[MinValueValidator(0)]
    )
    
    # Comments and notes
    reviewer_comments = models.TextField(_('reviewer comments'), blank=True)
    rejection_reason = models.TextField(_('rejection reason'), blank=True)
    internal_notes = models.TextField(_('internal notes'), blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'bursary_applications'
        verbose_name = _('Bursary Application')
        verbose_name_plural = _('Bursary Applications')
        ordering = ['-created_at']
        permissions = [
            ('can_review_application', 'Can review bursary application'),
            ('can_approve_application', 'Can approve bursary application'),
            ('can_disburse_funds', 'Can disburse bursary funds'),
        ]
    
    def __str__(self):
        return f"{self.application_number} - {self.applicant.get_full_name()}"
    
    def save(self, *args, **kwargs):
        # Only generate application number if it doesn't exist
        if not self.application_number and self.academic_year_id:
            try:
                # Generate unique application number
                year = self.academic_year.year.split('/')[0]
                prefix = f"BUR{year}"
            
                # Get the last application for this year
                last_app = BursaryApplication.objects.filter(
                    application_number__startswith=prefix
                ).order_by('-application_number').first()
            
                if last_app and last_app.application_number:
                    try:
                        # Extract the number part
                        last_number = int(last_app.application_number.replace(prefix, ''))
                        new_number = last_number + 1
                    except (ValueError, AttributeError):
                        new_number = 1
                else:
                    new_number = 1
            
                self.application_number = f"{prefix}{new_number:05d}"
            except Exception as e:
                # If there's any error, don't fail the save
                pass
    
        # Call parent save
        super().save(*args, **kwargs)


    
    @property
    def is_editable(self):
        return self.status in ['draft', 'rejected']
    
    @property
    def balance_needed(self):
        return self.total_fees - self.other_support - (self.approved_amount or 0)
    
    # Add these compatibility properties (but NOT user)
    @property
    def reference_number(self):
        """Alias for application_number for backward compatibility"""
        return self.application_number
    
    @property
    def institution_name(self):
        """Get institution name from either institution object or other field"""
        if self.institution:
            return self.institution.name
        return self.institution_name_other or "Not specified"



def application_document_path(instance, filename):
    """Generate upload path for application documents"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join(
        'applications',
        str(instance.application.academic_year.year),
        instance.application.application_number,
        filename
    )


class ApplicationDocument(models.Model):
    """
    Model for documents uploaded with bursary applications
    """
    DOCUMENT_TYPES = [
        # Mandatory for all applicants (NG-CDF order)
        ('transcript', "1. Student's Transcript / Report Form"),
        ('parent_id', "2. Parent's / Guardian's National ID Copy"),
        ('student_id', "3. Student's National ID Copy (mandatory post-school)"),
        ('birth_certificate', '4. Birth Certificate Copy'),
        ('school_id', '5. Secondary / College / University ID Card Copy'),
        ('death_certificate', '6. Death Certificate / Burial Permit (mandatory for orphans)'),
        ('fee_structure', '7. Current Fees Structure (mandatory for all)'),
        ('admission_letter', '8. Admission Letter (mandatory for colleges & universities)'),
        # Additional supporting documents
        ('disability_cert', 'Disability Certificate'),
        ('medical_report', 'Medical Report / Chronic Illness Evidence'),
        ('chief_letter', 'Verification Letter from Area Chief / Sub-Chief'),
        ('recommendation_letter', 'Recommendation Letter'),
        ('bank_slip', 'Bank Deposit Slip'),
        ('other', 'Other Supporting Document'),
    ]
    
    application = models.ForeignKey(
        BursaryApplication, 
        on_delete=models.CASCADE, 
        related_name='documents'
    )
    document_type = models.CharField(
        _('document type'), 
        max_length=30, 
        choices=DOCUMENT_TYPES
    )
    description = models.CharField(
        _('description'), 
        max_length=200, 
        blank=True
    )
    file = models.FileField(
        _('file'), 
        upload_to=application_document_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'jpg', 'jpeg', 'png']
            )
        ]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'application_documents'
        verbose_name = _('Application Document')
        verbose_name_plural = _('Application Documents')
        ordering = ['document_type', '-uploaded_at']
    
    def __str__(self):
        return f"{self.get_document_type_display()} - {self.application.application_number}"
    
    @property
    def file_size(self):
        return self.file.size
    
    @property
    def file_extension(self):
        return os.path.splitext(self.file.name)[1].lower()


class ApplicationStatusLog(models.Model):
    """
    Model to track status changes for applications
    """
    application = models.ForeignKey(
        BursaryApplication, 
        on_delete=models.CASCADE, 
        related_name='status_logs'
    )
    previous_status = models.CharField(
        _('previous status'), 
        max_length=20, 
        choices=BursaryApplication.STATUS_CHOICES
    )
    new_status = models.CharField(
        _('new status'), 
        max_length=20, 
        choices=BursaryApplication.STATUS_CHOICES
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True
    )
    comment = models.TextField(_('comment'), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'application_status_logs'
        verbose_name = _('Application Status Log')
        verbose_name_plural = _('Application Status Logs')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.application.application_number}: {self.previous_status} → {self.new_status}"


class Disbursement(models.Model):
    """
    Model to track bursary disbursements
    """
    PAYMENT_METHODS = [
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('mpesa', 'M-PESA'),
        ('cash', 'Cash'),
    ]
    
    application = models.ForeignKey(
        BursaryApplication, 
        on_delete=models.PROTECT, 
        related_name='disbursements'
    )
    amount = models.DecimalField(
        _('amount'), 
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    payment_method = models.CharField(
        _('payment method'), 
        max_length=20, 
        choices=PAYMENT_METHODS
    )
    reference_number = models.CharField(
        _('reference number'), 
        max_length=100, 
        unique=True
    )
    paid_to = models.CharField(
        _('paid to'), 
        max_length=200,
        help_text=_('Name of institution or recipient')
    )
    payment_date = models.DateField(_('payment date'))
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True
    )
    receipt_number = models.CharField(
        _('receipt number'), 
        max_length=100, 
        blank=True
    )
    notes = models.TextField(_('notes'), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'disbursements'
        verbose_name = _('Disbursement')
        verbose_name_plural = _('Disbursements')
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.reference_number} - KES {self.amount}"