from rest_framework import serializers
from .models import (
    BursaryApplication, ApplicationDocument, AcademicYear,
    Institution, ApplicationStatusLog, Disbursement
)
from accounts.serializers import UserSerializer


class AcademicYearSerializer(serializers.ModelSerializer):
    """Serializer for academic years"""
    class Meta:
        model = AcademicYear
        fields = '__all__'


class InstitutionSerializer(serializers.ModelSerializer):
    """Serializer for institutions"""
    application_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Institution
        fields = [
            'id', 'name', 'institution_type', 'county',
            'address', 'is_verified', 'application_count'
        ]


class ApplicationDocumentSerializer(serializers.ModelSerializer):
    """Serializer for application documents"""
    file_size = serializers.ReadOnlyField()
    file_extension = serializers.ReadOnlyField()
    
    class Meta:
        model = ApplicationDocument
        fields = [
            'id', 'document_type', 'description', 'file',
            'uploaded_at', 'file_size', 'file_extension'
        ]
        read_only_fields = ['uploaded_at']


class ApplicationStatusLogSerializer(serializers.ModelSerializer):
    """Serializer for status logs"""
    changed_by_name = serializers.CharField(source='changed_by.get_full_name', read_only=True)
    
    class Meta:
        model = ApplicationStatusLog
        fields = [
            'id', 'previous_status', 'new_status', 'changed_by',
            'changed_by_name', 'comment', 'created_at'
        ]


class BursaryApplicationListSerializer(serializers.ModelSerializer):
    """Serializer for application list view"""
    applicant_name = serializers.CharField(source='applicant.get_full_name', read_only=True)
    institution_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = BursaryApplication
        fields = [
            'id', 'application_number', 'applicant_name', 'education_level',
            'institution_name', 'amount_requested', 'status', 'status_display',
            'submitted_at', 'created_at'
        ]
    
    def get_institution_name(self, obj):
        if obj.institution:
            return obj.institution.name
        return obj.institution_name_other


class BursaryApplicationDetailSerializer(serializers.ModelSerializer):
    """Serializer for application detail view"""
    applicant = UserSerializer(read_only=True)
    academic_year = AcademicYearSerializer(read_only=True)
    institution = InstitutionSerializer(read_only=True)
    documents = ApplicationDocumentSerializer(many=True, read_only=True)
    status_logs = ApplicationStatusLogSerializer(many=True, read_only=True)
    education_level_display = serializers.CharField(source='get_education_level_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    balance_needed = serializers.ReadOnlyField()
    is_editable = serializers.ReadOnlyField()
    
    class Meta:
        model = BursaryApplication
        fields = '__all__'


class BursaryApplicationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating applications"""
    new_institution_name = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = BursaryApplication
        fields = [
            'education_level', 'institution', 'new_institution_name',
            'admission_number', 'course_name', 'year_of_study',
            'total_fees', 'amount_requested', 'other_support',
            'family_monthly_income', 'number_of_siblings',
            'siblings_in_school', 'is_orphan', 'is_single_parent',
            'has_disability', 'special_circumstances'
        ]
    
    def validate(self, attrs):
        # Validate institution selection
        institution = attrs.get('institution')
        new_institution_name = attrs.get('new_institution_name')
        
        if not institution and not new_institution_name:
            raise serializers.ValidationError(
                "Please select an institution or enter a new one."
            )
        
        # Validate financial information
        total_fees = attrs.get('total_fees', 0)
        amount_requested = attrs.get('amount_requested', 0)
        other_support = attrs.get('other_support', 0)
        
        if amount_requested > total_fees:
            raise serializers.ValidationError({
                'amount_requested': 'Amount requested cannot exceed total fees.'
            })
        
        if other_support > total_fees:
            raise serializers.ValidationError({
                'other_support': 'Other support cannot exceed total fees.'
            })
        
        # Validate sibling information
        number_of_siblings = attrs.get('number_of_siblings', 0)
        siblings_in_school = attrs.get('siblings_in_school', 0)
        
        if siblings_in_school > number_of_siblings:
            raise serializers.ValidationError({
                'siblings_in_school': 'Siblings in school cannot exceed total number of siblings.'
            })
        
        return attrs
    
    def create(self, validated_data):
        new_institution_name = validated_data.pop('new_institution_name', None)
        
        # Get active academic year
        academic_year = AcademicYear.objects.filter(is_active=True).first()
        if not academic_year:
            raise serializers.ValidationError("No active academic year found.")
        
        # Create application
        application = BursaryApplication.objects.create(
            applicant=self.context['request'].user,
            academic_year=academic_year,
            institution_name_other=new_institution_name if new_institution_name and not validated_data.get('institution') else '',
            **validated_data
        )
        
        return application


class ApplicationReviewSerializer(serializers.Serializer):
    """Serializer for reviewing applications"""
    status = serializers.ChoiceField(choices=['verified', 'approved', 'rejected'])
    approved_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False
    )
    comments = serializers.CharField(required=False, allow_blank=True)
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        status = attrs.get('status')
        
        if status == 'approved':
            if not attrs.get('approved_amount'):
                raise serializers.ValidationError({
                    'approved_amount': 'Approved amount is required when approving.'
                })
        elif status == 'rejected':
            if not attrs.get('rejection_reason'):
                raise serializers.ValidationError({
                    'rejection_reason': 'Rejection reason is required when rejecting.'
                })
        
        return attrs


class DisbursementSerializer(serializers.ModelSerializer):
    """Serializer for disbursements"""
    application_number = serializers.CharField(
        source='application.application_number',
        read_only=True
    )
    applicant_name = serializers.CharField(
        source='application.applicant.get_full_name',
        read_only=True
    )
    processed_by_name = serializers.CharField(
        source='processed_by.get_full_name',
        read_only=True
    )
    
    class Meta:
        model = Disbursement
        fields = [
            'id', 'application', 'application_number', 'applicant_name',
            'amount', 'payment_method', 'reference_number', 'paid_to',
            'payment_date', 'processed_by', 'processed_by_name',
            'receipt_number', 'notes', 'created_at'
        ]
        read_only_fields = ['processed_by', 'created_at']


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics"""
    total_applications = serializers.IntegerField()
    pending_applications = serializers.IntegerField()
    approved_applications = serializers.IntegerField()
    total_approved_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    pending_review = serializers.IntegerField(required=False)
    under_review = serializers.IntegerField(required=False)
    approved_today = serializers.IntegerField(required=False)
    total_requested = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    total_disbursed = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    can_apply = serializers.BooleanField(required=False)
    active_year = AcademicYearSerializer(required=False)
    recent_applications = BursaryApplicationListSerializer(many=True, required=False)