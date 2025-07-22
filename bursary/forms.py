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
    Main form for bursary applications
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
            'education_level', 'institution', 'admission_number',
            'course_name', 'year_of_study', 'total_fees',
            'amount_requested', 'other_support', 'family_monthly_income',
            'number_of_siblings', 'siblings_in_school', 'is_orphan',
            'is_single_parent', 'has_disability', 'special_circumstances'
        ]
        widgets = {
            'education_level': forms.Select(attrs={'class': 'form-control'}),
            'institution': forms.Select(attrs={'class': 'form-control'}),
            'admission_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2024/001'
            }),
            'course_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Form 2, BSc Computer Science'
            }),
            'year_of_study': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '10'
            }),
            'total_fees': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'amount_requested': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'other_support': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'family_monthly_income': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'number_of_siblings': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'siblings_in_school': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'is_orphan': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_single_parent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_disability': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'special_circumstances': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe any special circumstances affecting your need for bursary'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter institutions based on education level if editing
        if self.instance.pk and self.instance.education_level:
            self.fields['institution'].queryset = Institution.objects.filter(
                institution_type=self._get_institution_type()
            )
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.layout = Layout(
            Alert(
                content='Please fill in all required fields accurately. False information may lead to disqualification.',
                css_class='alert-info'
            ),
            
            Fieldset(
                'Educational Information',
                Row(
                    Column('education_level', css_class='col-md-6'),
                    Column('year_of_study', css_class='col-md-6'),
                ),
                Row(
                    Column('institution', css_class='col-md-6'),
                    Column('new_institution_name', css_class='col-md-6'),
                ),
                Row(
                    Column('admission_number', css_class='col-md-6'),
                    Column('course_name', css_class='col-md-6'),
                ),
                css_class='mb-4'
            ),
            
            Fieldset(
                'Financial Information',
                Row(
                    Column('total_fees', css_class='col-md-4'),
                    Column('amount_requested', css_class='col-md-4'),
                    Column('other_support', css_class='col-md-4'),
                ),
                HTML('<small class="text-muted mb-3 d-block">All amounts should be in Kenya Shillings (KES)</small>'),
                css_class='mb-4'
            ),
            
            Fieldset(
                'Family Background',
                Row(
                    Column('family_monthly_income', css_class='col-md-4'),
                    Column('number_of_siblings', css_class='col-md-4'),
                    Column('siblings_in_school', css_class='col-md-4'),
                ),
                css_class='mb-4'
            ),
            
            Fieldset(
                'Special Circumstances',
                Row(
                    Column(
                        Div(
                            Field('is_orphan'),
                            css_class='form-check'
                        ),
                        css_class='col-md-4'
                    ),
                    Column(
                        Div(
                            Field('is_single_parent'),
                            css_class='form-check'
                        ),
                        css_class='col-md-4'
                    ),
                    Column(
                        Div(
                            Field('has_disability'),
                            css_class='form-check'
                        ),
                        css_class='col-md-4'
                    ),
                ),
                Field('special_circumstances'),
                css_class='mb-4'
            ),
            
            Row(
                Column(
                    Submit('save_draft', 'Save as Draft', css_class='btn btn-secondary'),
                    css_class='col-6'
                ),
                Column(
                    Submit('submit_application', 'Submit Application', css_class='btn btn-primary'),
                    css_class='col-6 text-end'
                ),
            )
        )
    
    def _get_institution_type(self):
        """Map education level to institution type"""
        mapping = {
            'primary': 'primary',
            'secondary': 'secondary',
            'tvet': 'tvet',
            'undergraduate': 'university',
            'postgraduate': 'university',
        }
        return mapping.get(self.instance.education_level, 'other')
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate institution selection
        institution = cleaned_data.get('institution')
        new_institution_name = cleaned_data.get('new_institution_name')
        
        if not institution and not new_institution_name:
            raise ValidationError(
                _('Please select an institution or enter a new one')
            )
        
        # Validate financial information
        total_fees = cleaned_data.get('total_fees', 0)
        amount_requested = cleaned_data.get('amount_requested', 0)
        other_support = cleaned_data.get('other_support', 0)
        
        if amount_requested > total_fees:
            raise ValidationError({
                'amount_requested': _('Amount requested cannot exceed total fees')
            })
        
        if other_support > total_fees:
            raise ValidationError({
                'other_support': _('Other support cannot exceed total fees')
            })
        
        # Validate sibling information
        number_of_siblings = cleaned_data.get('number_of_siblings', 0)
        siblings_in_school = cleaned_data.get('siblings_in_school', 0)
        
        if siblings_in_school > number_of_siblings:
            raise ValidationError({
                'siblings_in_school': _('Siblings in school cannot exceed total number of siblings')
            })
        
        return cleaned_data
    
    def save(self, commit=True):
        application = super().save(commit=False)
        
        # Handle new institution
        new_institution_name = self.cleaned_data.get('new_institution_name')
        if new_institution_name and not application.institution:
            application.institution_name_other = new_institution_name
        
        # DON'T save here - let the view handle it
        # The view needs to set applicant and academic_year first
        # if commit:
        #     application.save()
        
        return application


class ApplicationDocumentForm(forms.ModelForm):
    """
    Form for uploading application documents
    """
    class Meta:
        model = ApplicationDocument
        fields = ['document_type', 'description', 'file']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief description (optional)'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
        }
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        
        if file:
            # Check file size
            if file.size > settings.MAX_UPLOAD_SIZE:
                raise ValidationError(
                    _('File size must not exceed %(size)s MB') % {
                        'size': settings.MAX_UPLOAD_SIZE / (1024 * 1024)
                    }
                )
            
            # Check file extension
            ext = file.name.split('.')[-1].lower()
            if ext not in settings.ALLOWED_DOCUMENT_TYPES:
                raise ValidationError(
                    _('File type not allowed. Allowed types: %(types)s') % {
                        'types': ', '.join(settings.ALLOWED_DOCUMENT_TYPES)
                    }
                )
        
        return file


class ApplicationReviewForm(forms.Form):
    """
    Form for reviewing applications (admin use)
    """
    STATUS_CHOICES = [
        ('verified', 'Verify Application'),
        ('approved', 'Approve Application'),
        ('rejected', 'Reject Application'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    approved_amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter approved amount',
            'step': '0.01'
        })
    )
    comments = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Enter review comments'
        })
    )
    rejection_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Reason for rejection (required if rejecting)'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.application = kwargs.pop('application', None)
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('status'),
            Div(
                Field('approved_amount'),
                css_id='approved_amount_div',
                css_class='d-none'
            ),
            Field('comments'),
            Div(
                Field('rejection_reason'),
                css_id='rejection_reason_div',
                css_class='d-none'
            ),
            Submit('submit', 'Submit Review', css_class='btn btn-primary')
        )
    
    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        
        if status == 'approved':
            approved_amount = cleaned_data.get('approved_amount')
            if not approved_amount:
                raise ValidationError({
                    'approved_amount': _('Approved amount is required when approving')
                })
            
            if self.application and approved_amount > self.application.amount_requested:
                raise ValidationError({
                    'approved_amount': _('Approved amount cannot exceed requested amount')
                })
        
        elif status == 'rejected':
            rejection_reason = cleaned_data.get('rejection_reason')
            if not rejection_reason:
                raise ValidationError({
                    'rejection_reason': _('Rejection reason is required when rejecting')
                })
        
        return cleaned_data


class ApplicationFilterForm(forms.Form):
    """
    Form for filtering applications in admin dashboard
    """
    STATUS_CHOICES = [('', 'All Statuses')] + BursaryApplication.STATUS_CHOICES
    EDUCATION_CHOICES = [('', 'All Levels')] + BursaryApplication.EDUCATION_LEVEL_CHOICES
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    education_level = forms.ChoiceField(
        choices=EDUCATION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, application number, or ID number'
        })
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )