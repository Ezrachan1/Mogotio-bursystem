from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, Div, HTML, Fieldset
from crispy_forms.bootstrap import Alert
from .models import BursaryApplication, ApplicationDocument, Institution
from django.conf import settings


class BursaryApplicationForm(forms.ModelForm):
    """
    Comprehensive NG-CDF standard bursary application form.
    Organized into sections matching the official paper form.
    """
    # Additional field for new institutions
    new_institution_name = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter institution name if not in list'
        })
    )

    class Meta:
        model = BursaryApplication
        fields = [
            # Part A: Personal & Institutional
            'education_level', 'institution', 'admission_number',
            'course_name', 'year_of_study', 'campus_branch',
            'faculty_department', 'mode_of_study', 'course_duration',
            'expected_completion',
            # Financial
            'total_fees', 'amount_requested', 'other_support',
            # Family Status
            'family_status', 'family_status_other',
            'family_monthly_income', 'family_annual_income', 'family_annual_expenses',
            'number_of_siblings', 'siblings_in_school',
            # Special Circumstances
            'is_orphan', 'is_single_parent', 'has_disability',
            'special_circumstances',
            # Father
            'father_name', 'father_address', 'father_telephone',
            'father_occupation', 'father_employment_type', 'father_income_source',
            # Mother
            'mother_name', 'mother_address', 'mother_telephone',
            'mother_occupation', 'mother_employment_type', 'mother_income_source',
            # Guardian
            'app_guardian_name', 'app_guardian_address', 'app_guardian_telephone',
            'app_guardian_occupation', 'app_guardian_employment_type', 'app_guardian_income_source',
            # Additional Info
            'reason_for_applying',
            'previous_cdf_support', 'previous_cdf_support_details',
            'previous_other_support_received', 'previous_other_support_details',
            'disability_details', 'has_chronic_illness', 'chronic_illness_details',
            'parent_has_disability', 'parent_disability_details',
            'parent_has_chronic_illness', 'parent_chronic_illness_details',
            # Academic Performance
            'academic_performance', 'been_sent_away', 'sent_away_reasons', 'sent_away_weeks',
            'annual_fees_per_structure', 'last_term_balance',
            'current_term_balance', 'next_term_balance', 'helb_loan_amount',
            # Funding History
            'funding_source_secondary', 'funding_source_college', 'funding_source_university',
            'other_funding_secondary', 'other_funding_college', 'other_funding_university',
            # Referees
            'referee1_name', 'referee1_address', 'referee1_telephone',
            'referee2_name', 'referee2_address', 'referee2_telephone',
        ]
        widgets = {
            'education_level': forms.Select(attrs={'class': 'form-select'}),
            'institution': forms.Select(attrs={'class': 'form-select'}),
            'admission_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 2024/001'}),
            'course_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Form 2, BSc Computer Science'}),
            'year_of_study': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '10'}),
            'campus_branch': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Campus or branch name'}),
            'faculty_department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Faculty / Department'}),
            'mode_of_study': forms.Select(attrs={'class': 'form-select'}),
            'course_duration': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '10', 'placeholder': 'Years'}),
            'expected_completion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'MM/YYYY'}),
            # Financial
            'total_fees': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            'amount_requested': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            'other_support': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            # Family
            'family_status': forms.Select(attrs={'class': 'form-select'}),
            'family_status_other': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Specify other status'}),
            'family_monthly_income': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            'family_annual_income': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Annual income KES', 'step': '0.01'}),
            'family_annual_expenses': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Annual expenses KES', 'step': '0.01'}),
            'number_of_siblings': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'siblings_in_school': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            # Checkboxes
            'is_orphan': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_single_parent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_disability': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'special_circumstances': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            # Father
            'father_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name'}),
            'father_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address'}),
            'father_telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+254...'}),
            'father_occupation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Occupation'}),
            'father_employment_type': forms.Select(attrs={'class': 'form-select'}),
            'father_income_source': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Main source of income'}),
            # Mother
            'mother_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name'}),
            'mother_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address'}),
            'mother_telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+254...'}),
            'mother_occupation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Occupation'}),
            'mother_employment_type': forms.Select(attrs={'class': 'form-select'}),
            'mother_income_source': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Main source of income'}),
            # Guardian
            'app_guardian_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name'}),
            'app_guardian_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address'}),
            'app_guardian_telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+254...'}),
            'app_guardian_occupation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Occupation'}),
            'app_guardian_employment_type': forms.Select(attrs={'class': 'form-select'}),
            'app_guardian_income_source': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Main source of income'}),
            # Additional
            'reason_for_applying': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Why are you applying for bursary assistance?'}),
            'previous_cdf_support': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'previous_cdf_support_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Amount and when'}),
            'previous_other_support_received': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'previous_other_support_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Details'}),
            'disability_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Describe disability'}),
            'has_chronic_illness': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'chronic_illness_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'parent_has_disability': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'parent_disability_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'parent_has_chronic_illness': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'parent_chronic_illness_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            # Academic
            'academic_performance': forms.Select(attrs={'class': 'form-select'}),
            'been_sent_away': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sent_away_reasons': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'sent_away_weeks': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'annual_fees_per_structure': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'last_term_balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'current_term_balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'next_term_balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'helb_loan_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'If applicable'}),
            # Funding history
            'funding_source_secondary': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Parents, Bursary, HELB'}),
            'funding_source_college': forms.TextInput(attrs={'class': 'form-control'}),
            'funding_source_university': forms.TextInput(attrs={'class': 'form-control'}),
            'other_funding_secondary': forms.TextInput(attrs={'class': 'form-control'}),
            'other_funding_college': forms.TextInput(attrs={'class': 'form-control'}),
            'other_funding_university': forms.TextInput(attrs={'class': 'form-control'}),
            # Referees
            'referee1_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name'}),
            'referee1_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address'}),
            'referee1_telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+254...'}),
            'referee2_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name'}),
            'referee2_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address'}),
            'referee2_telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+254...'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Institution is optional — user can type a new one
        self.fields['institution'].required = False

        # Filter institutions based on education level if editing
        if self.instance.pk and self.instance.education_level:
            self.fields['institution'].queryset = Institution.objects.filter(
                institution_type=self._get_institution_type()
            )

        # Only require core fields; rest are optional for draft saves
        optional_fields = [
            'campus_branch', 'faculty_department', 'mode_of_study',
            'course_duration', 'expected_completion', 'family_status',
            'family_status_other', 'family_annual_income', 'family_annual_expenses',
            'father_name', 'father_address', 'father_telephone', 'father_occupation',
            'father_employment_type', 'father_income_source',
            'mother_name', 'mother_address', 'mother_telephone', 'mother_occupation',
            'mother_employment_type', 'mother_income_source',
            'app_guardian_name', 'app_guardian_address', 'app_guardian_telephone',
            'app_guardian_occupation', 'app_guardian_employment_type', 'app_guardian_income_source',
            'reason_for_applying', 'previous_cdf_support_details',
            'previous_other_support_details', 'disability_details',
            'chronic_illness_details', 'parent_disability_details',
            'parent_chronic_illness_details',
            'academic_performance', 'sent_away_reasons', 'sent_away_weeks',
            'annual_fees_per_structure', 'last_term_balance', 'current_term_balance',
            'next_term_balance', 'helb_loan_amount',
            'funding_source_secondary', 'funding_source_college', 'funding_source_university',
            'other_funding_secondary', 'other_funding_college', 'other_funding_university',
            'referee1_name', 'referee1_address', 'referee1_telephone',
            'referee2_name', 'referee2_address', 'referee2_telephone',
            'special_circumstances', 'other_support', 'new_institution_name',
        ]
        for field_name in optional_fields:
            if field_name in self.fields:
                self.fields[field_name].required = False

        # Template provides <form> tag and buttons
        self.helper = FormHelper()
        self.helper.form_tag = False

    def _get_institution_type(self):
        mapping = {
            'primary': 'primary', 'secondary': 'secondary', 'tvet': 'tvet',
            'undergraduate': 'university', 'postgraduate': 'university',
        }
        return mapping.get(self.instance.education_level, 'other')

    def clean(self):
        cleaned_data = super().clean()
        institution = cleaned_data.get('institution')
        new_institution_name = cleaned_data.get('new_institution_name')
        if not institution and not new_institution_name:
            raise ValidationError(_('Please select an institution or enter a new one'))

        total_fees = cleaned_data.get('total_fees', 0) or 0
        amount_requested = cleaned_data.get('amount_requested', 0) or 0
        other_support = cleaned_data.get('other_support', 0) or 0
        if amount_requested > total_fees:
            raise ValidationError({'amount_requested': _('Cannot exceed total fees')})
        if other_support > total_fees:
            raise ValidationError({'other_support': _('Cannot exceed total fees')})

        number_of_siblings = cleaned_data.get('number_of_siblings', 0) or 0
        siblings_in_school = cleaned_data.get('siblings_in_school', 0) or 0
        if siblings_in_school > number_of_siblings:
            raise ValidationError({'siblings_in_school': _('Cannot exceed total siblings')})
        return cleaned_data

    def save(self, commit=True):
        application = super().save(commit=False)
        new_institution_name = self.cleaned_data.get('new_institution_name')
        if new_institution_name and not application.institution:
            application.institution_name_other = new_institution_name
        if commit:
            application.save()
        return application


class ApplicationDocumentForm(forms.ModelForm):
    class Meta:
        model = ApplicationDocument
        fields = ['document_type', 'description', 'file']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brief description (optional)'}),
            'file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'}),
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            if file.size > settings.MAX_UPLOAD_SIZE:
                raise ValidationError(
                    _('File size must not exceed %(size)s MB') % {'size': settings.MAX_UPLOAD_SIZE / (1024 * 1024)})
            ext = file.name.split('.')[-1].lower()
            if ext not in settings.ALLOWED_DOCUMENT_TYPES:
                raise ValidationError(
                    _('Allowed types: %(types)s') % {'types': ', '.join(settings.ALLOWED_DOCUMENT_TYPES)})
        return file


class ApplicationReviewForm(forms.Form):
    STATUS_CHOICES = [
        ('verified', 'Verify Application'),
        ('approved', 'Approve Application'),
        ('rejected', 'Reject Application'),
    ]
    status = forms.ChoiceField(choices=STATUS_CHOICES, widget=forms.RadioSelect(attrs={'class': 'form-check-input'}))
    approved_amount = forms.DecimalField(max_digits=10, decimal_places=2, required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Approved amount', 'step': '0.01'}))
    comments = forms.CharField(required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Review comments'}))
    rejection_reason = forms.CharField(required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Reason for rejection'}))

    def __init__(self, *args, **kwargs):
        self.application = kwargs.pop('application', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Filter choices based on user role
        if self.user:
            if self.user.can_approve_applications:
                # Admin/Approver: can verify, approve, or reject
                allowed = [('verified', 'Verify Application'),
                           ('approved', 'Approve Application'),
                           ('rejected', 'Reject Application')]
            else:
                # Reviewer: can only verify or reject — cannot approve
                allowed = [('verified', 'Verify Application'),
                           ('rejected', 'Reject Application')]
            self.fields['status'].choices = allowed

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('status'),
            Div(Field('approved_amount'), css_id='approved_amount_div', css_class='d-none'),
            Field('comments'),
            Div(Field('rejection_reason'), css_id='rejection_reason_div', css_class='d-none'),
            Submit('submit', 'Submit Review', css_class='btn btn-primary')
        )

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')

        # Server-side role enforcement
        if status == 'approved' and self.user and not self.user.can_approve_applications:
            raise ValidationError(
                _('You do not have permission to approve applications. Only approvers and admins can approve.'))

        if status == 'approved':
            approved_amount = cleaned_data.get('approved_amount')
            if not approved_amount:
                raise ValidationError({'approved_amount': _('Required when approving')})
            if self.application and approved_amount > self.application.amount_requested:
                raise ValidationError({'approved_amount': _('Cannot exceed requested amount')})
        elif status == 'rejected':
            if not cleaned_data.get('rejection_reason'):
                raise ValidationError({'rejection_reason': _('Required when rejecting')})
        return cleaned_data


class ApplicationFilterForm(forms.Form):
    STATUS_CHOICES = [('', 'All Statuses')] + BursaryApplication.STATUS_CHOICES
    EDUCATION_CHOICES = [('', 'All Levels')] + BursaryApplication.EDUCATION_LEVEL_CHOICES
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    education_level = forms.ChoiceField(choices=EDUCATION_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    search = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search...'}))
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
