from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import login
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView,
    TemplateView, FormView, View
)
from django.db.models import Q, Sum, Count, Avg
from django.http import HttpResponse, JsonResponse, Http404
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime, timedelta
import csv

from .models import (
    BursaryApplication, ApplicationDocument, AcademicYear,
    Institution, ApplicationStatusLog, Disbursement
)
from .forms import (
    BursaryApplicationForm, ApplicationDocumentForm,
    ApplicationReviewForm, ApplicationFilterForm
)
from .utils import (
    send_application_submitted_notification,
    send_application_status_notification,
    calculate_bursary_score,
    export_applications_to_csv,
    generate_application_report,
    EmailVerificationService
)


class DashboardView(LoginRequiredMixin, TemplateView):
    """Main dashboard view - different content based on user role"""
    template_name = 'bursary/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_applicant:
            # Applicant dashboard
            applications = BursaryApplication.objects.filter(
                applicant=user
            ).select_related('academic_year', 'institution')

            context['applications'] = applications
            context['recent_applications'] = applications.order_by('-created_at')[:10]
            context['total_applications'] = applications.count()
            context['pending_applications'] = applications.filter(
                status__in=['draft', 'submitted', 'under_review']
            ).count()
            context['approved_applications'] = applications.filter(
                status='approved'
            ).count()
            context['total_approved_amount'] = applications.filter(
                status='approved'
            ).aggregate(Sum('approved_amount'))['approved_amount__sum'] or 0

            # Check if user can apply
            active_year = AcademicYear.objects.filter(
                is_active=True,
                application_deadline__gt=timezone.now()
            ).first()
            context['can_apply'] = active_year is not None and user.is_verified
            context['active_year'] = active_year

        elif user.can_review_applications:
            # Staff dashboard
            all_applications = BursaryApplication.objects.all()

            context['total_applications'] = all_applications.count()
            context['pending_review'] = all_applications.filter(
                status='submitted'
            ).count()
            context['under_review'] = all_applications.filter(
                status='under_review'
            ).count()
            context['approved_today'] = all_applications.filter(
                status='approved',
                approved_at__date=timezone.now().date()
            ).count()

            # Recent applications
            context['recent_submissions'] = all_applications.select_related(
                'applicant', 'academic_year', 'institution'
            ).order_by('-submitted_at')[:10]

            # Statistics
            context['total_requested'] = all_applications.aggregate(
                Sum('amount_requested')
            )['amount_requested__sum'] or 0
            context['total_approved'] = all_applications.filter(
                status='approved'
            ).aggregate(Sum('approved_amount'))['approved_amount__sum'] or 0

        return context


# Applicant Views
class ApplicationListView(LoginRequiredMixin, ListView):
    """List user's applications"""
    model = BursaryApplication
    template_name = 'bursary/application_list.html'
    context_object_name = 'applications'
    paginate_by = 10

    def get_queryset(self):
        return BursaryApplication.objects.filter(
            applicant=self.request.user
        ).select_related('academic_year', 'institution').order_by('-created_at')


class ApplicationCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create new bursary application"""
    model = BursaryApplication
    form_class = BursaryApplicationForm
    template_name = 'bursary/application_form.html'

    def test_func(self):
        # Skip verification check for admin/staff users
        if not (self.request.user.is_staff or self.request.user.is_superuser):
            # Check if regular user is verified
            if not self.request.user.is_verified:
                messages.error(
                    self.request,
                    'Please verify your phone number before applying.'
                )
                return False

        # Check for active academic year
        active_year = AcademicYear.objects.filter(
            is_active=True,
            application_deadline__gt=timezone.now()
        ).first()

        if not active_year:
            messages.error(
                self.request,
                'No active application period at the moment. Please ensure there is an active academic year with a future deadline.'
            )
            return False

        # Check if user already has an application for this year
        existing = BursaryApplication.objects.filter(
            applicant=self.request.user,
            academic_year=active_year
        ).exists()

        if existing:
            messages.error(
                self.request,
                'You already have an application for this academic year.'
            )
            return False

        return True

    def handle_no_permission(self):
        """Override to redirect instead of showing 403 page"""
        if not self.request.user.is_authenticated:
            return redirect('accounts:login')

        # Check specific reason for denial and redirect appropriately
        if not self.request.user.is_verified and not (self.request.user.is_staff or self.request.user.is_superuser):
            return redirect('accounts:verify_email')
        else:
            # For admin users or other cases, redirect to dashboard
            return redirect('bursary:dashboard')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Get active academic year
        active_year = AcademicYear.objects.filter(
            is_active=True,
            application_deadline__gt=timezone.now()
        ).first()

        if not active_year:
            messages.error(
                self.request,
                'No active academic year found. Please contact the administrator.'
            )
            return redirect('bursary:application_list')

        # Set required fields on the form instance
        form.instance.applicant = self.request.user
        form.instance.academic_year = active_year
        form.instance.status = 'draft'  # ALWAYS draft in step 1

        # Save the form and create the object
        # It's important to call super().form_valid(form) first
        # so self.object is populated.
        response = super().form_valid(form)

        # Now self.object exists with a valid pk
        # Create status log
        try:
            ApplicationStatusLog.objects.create(
                application=self.object,
                previous_status='',
                new_status='draft',
                changed_by=self.request.user,
                comment='Application created'
            )
        except Exception:
            pass  # Don't fail if log creation fails

        # Show appropriate message based on button clicked
        if 'save_draft' in self.request.POST:
            messages.success(
                self.request,
                f'Application {self.object.application_number} saved as draft. You can continue editing later.'
            )
        else:
            # save_continue button clicked
            messages.success(
                self.request,
                f'Application {self.object.application_number} saved successfully. Please upload the required documents.'
            )

        return response

    def get_success_url(self):
        """Determine where to redirect after successful form submission"""
        # Check if we have a valid object with pk
        if hasattr(self, 'object') and self.object and self.object.pk:
            if 'save_draft' in self.request.POST:
                # Save draft - go to application list
                return reverse_lazy('bursary:application_list')
            else:
                # Save and continue - go to document upload (step 2)
                return reverse_lazy('bursary:document_upload', kwargs={'pk': self.object.pk})
        else:
            # Fallback if something goes wrong
            messages.error(self.request, 'An error occurred. Please try again.')
            return reverse_lazy('bursary:application_list')


class ApplicationDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """View application details"""
    model = BursaryApplication
    template_name = 'bursary/application_detail.html'
    context_object_name = 'application'

    def test_func(self):
        application = self.get_object()
        return (
            application.applicant == self.request.user or
            self.request.user.can_review_applications
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['documents'] = self.object.documents.all()
        context['status_logs'] = self.object.status_logs.all().order_by('-created_at')
        context['bursary_score'] = calculate_bursary_score(self.object)
        context['review_form'] = ApplicationReviewForm(application=self.object)

        # Similar applications (same ward, education level)
        context['similar_applications'] = BursaryApplication.objects.filter(
            applicant__ward=self.object.applicant.ward,
            education_level=self.object.education_level,
            academic_year=self.object.academic_year
        ).exclude(id=self.object.id)[:5]

        return context


class ApplicationReviewView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    """Review and update application status"""
    form_class = ApplicationReviewForm
    template_name = 'bursary/application_review.html'

    def test_func(self):
        return self.request.user.can_review_applications

    def get_application(self):
        return get_object_or_404(BursaryApplication, pk=self.kwargs['pk'])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['application'] = self.get_application()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        application = self.get_application()
        context['application'] = application
        # FormView passes the form as 'form' — template expects 'review_form'
        context['review_form'] = context.get('form')
        # Calculate bursary score
        context['bursary_score'] = calculate_bursary_score(application)

        # Documents in NG-CDF order (by DOCUMENT_TYPES list position)
        type_order = [t[0] for t in ApplicationDocument.DOCUMENT_TYPES]
        docs = list(application.documents.all())
        docs.sort(key=lambda d: type_order.index(d.document_type) if d.document_type in type_order else 999)
        context['documents_ordered'] = docs

        # Figure out which required docs are missing
        uploaded_types = set(d.document_type for d in docs)
        required = ['transcript', 'parent_id', 'birth_certificate', 'fee_structure']
        if application.education_level in ('tvet', 'undergraduate', 'postgraduate'):
            required.extend(['student_id', 'admission_letter'])
        if application.education_level in ('secondary', 'tvet', 'undergraduate', 'postgraduate'):
            required.append('school_id')
        if application.is_orphan:
            required.append('death_certificate')
        if application.has_disability:
            required.append('disability_cert')
        doc_labels = dict(ApplicationDocument.DOCUMENT_TYPES)
        context['missing_doc_types'] = [doc_labels.get(d, d) for d in required if d not in uploaded_types]

        return context

    def form_valid(self, form):
        application = self.get_application()
        old_status = application.status
        new_status = form.cleaned_data['status']

        # Extra server-side guard: only approvers can approve
        if new_status == 'approved' and not self.request.user.can_approve_applications:
            messages.error(self.request, 'You do not have permission to approve applications.')
            return redirect('bursary:application_review', pk=application.pk)

        # Update application
        application.status = new_status
        application.reviewer_comments = form.cleaned_data.get('comments', '')

        if new_status == 'verified':
            application.reviewed_by = self.request.user
            application.reviewed_at = timezone.now()
        elif new_status == 'approved':
            application.approved_by = self.request.user
            application.approved_at = timezone.now()
            application.approved_amount = form.cleaned_data['approved_amount']
        elif new_status == 'rejected':
            application.reviewed_by = self.request.user
            application.reviewed_at = timezone.now()
            application.rejection_reason = form.cleaned_data['rejection_reason']

        application.save()

        # Create status log
        ApplicationStatusLog.objects.create(
            application=application,
            previous_status=old_status,
            new_status=new_status,
            changed_by=self.request.user,
            comment=form.cleaned_data.get('comments', '')
        )

        # Send notification
        send_application_status_notification(application, old_status, new_status)

        messages.success(
            self.request,
            f'Application {application.application_number} has been {new_status}.'
        )

        return redirect('bursary:admin_application_list')


# Reports and Analytics
class ReportsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Reports and analytics dashboard"""
    template_name = 'bursary/reports.html'

    def test_func(self):
        return self.request.user.can_review_applications

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        import json
        from django.db.models.functions import TruncMonth

        # Get academic year filter
        year_id = self.request.GET.get('year')
        active_year = None
        if year_id:
            active_year = AcademicYear.objects.filter(pk=year_id).first()
        if not active_year:
            active_year = AcademicYear.objects.filter(is_active=True).first()

        context['active_year'] = active_year
        context['academic_years'] = AcademicYear.objects.all().order_by('-year')

        # Base queryset
        if active_year:
            apps = BursaryApplication.objects.filter(academic_year=active_year)
        else:
            apps = BursaryApplication.objects.all()

        total = apps.count()
        if total == 0:
            context['report_data'] = None
            return context

        # === Summary stats ===
        total_requested = apps.aggregate(s=Sum('amount_requested'))['s'] or 0
        total_approved = apps.filter(status__in=['approved', 'disbursed']).aggregate(s=Sum('approved_amount'))['s'] or 0
        avg_requested = apps.aggregate(a=Avg('amount_requested'))['a'] or 0

        context['report_data'] = {
            'total_applications': total,
            'total_requested': total_requested,
            'total_approved': total_approved,
            'average_requested': avg_requested,
        }

        # === Status distribution (for chart) ===
        status_counts = {}
        for code, label in BursaryApplication.STATUS_CHOICES:
            c = apps.filter(status=code).count()
            if c > 0:
                status_counts[label] = c
        context['status_chart_labels'] = json.dumps(list(status_counts.keys()))
        context['status_chart_data'] = json.dumps(list(status_counts.values()))

        # === Education level distribution (for chart) ===
        edu_counts = {}
        for code, label in BursaryApplication.EDUCATION_LEVEL_CHOICES:
            c = apps.filter(education_level=code).count()
            if c > 0:
                edu_counts[label] = c
        context['education_chart_labels'] = json.dumps(list(edu_counts.keys()))
        context['education_chart_data'] = json.dumps(list(edu_counts.values()))

        # === Ward distribution ===
        context['ward_distribution'] = apps.values(
            'applicant__ward'
        ).annotate(
            count=Count('id'),
            total_requested=Sum('amount_requested'),
            total_approved=Sum('approved_amount')
        ).order_by('-count')[:10]

        # === Institution distribution ===
        context['institution_distribution'] = apps.exclude(
            institution__isnull=True
        ).values(
            'institution__name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:10]

        # === Special cases ===
        context['special_cases'] = {
            'orphans': apps.filter(is_orphan=True).count(),
            'single_parent': apps.filter(is_single_parent=True).count(),
            'disabled': apps.filter(has_disability=True).count(),
        }

        # === Monthly trends ===
        monthly = apps.filter(
            submitted_at__isnull=False
        ).annotate(
            month=TruncMonth('submitted_at')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')

        month_labels = []
        month_data = []
        for entry in monthly:
            if entry['month']:
                month_labels.append(entry['month'].strftime('%b %Y'))
                month_data.append(entry['count'])
        context['monthly_labels'] = json.dumps(month_labels)
        context['monthly_data'] = json.dumps(month_data)

        # === Education level approval rates ===
        education_stats = []
        for level, label in BursaryApplication.EDUCATION_LEVEL_CHOICES:
            level_apps = apps.filter(education_level=level)
            t = level_apps.count()
            a = level_apps.filter(status__in=['approved', 'disbursed']).count()
            if t > 0:
                education_stats.append({
                    'level': label,
                    'total': t,
                    'approved': a,
                    'approval_rate': round((a / t) * 100, 1)
                })
        context['education_stats'] = education_stats

        return context


class ExportApplicationsView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Export applications to CSV"""
    def test_func(self):
        return self.request.user.can_review_applications

    def get(self, request):
        import csv

        # Get filtered queryset
        queryset = BursaryApplication.objects.select_related(
            'applicant', 'academic_year', 'institution'
        ).exclude(status='draft')

        # Apply filters
        status_filter = request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        education_filter = request.GET.get('education_level')
        if education_filter:
            queryset = queryset.filter(education_level=education_filter)
        year_filter = request.GET.get('year')
        if year_filter:
            queryset = queryset.filter(academic_year_id=year_filter)

        # Build CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="bursary_applications.csv"'
        writer = csv.writer(response)

        # Headers
        writer.writerow([
            'Application #', 'Academic Year', 'Applicant Name', 'ID Number',
            'Phone', 'Email', 'Ward', 'Location', 'Education Level',
            'Institution', 'Course', 'Year of Study',
            'Total Fees', 'Amount Requested', 'Other Support', 'Approved Amount',
            'Family Monthly Income', 'No. of Siblings', 'Siblings in School',
            'Is Orphan', 'Single Parent', 'Disability', 'Family Status',
            'Academic Performance', 'Previous CDF Support',
            'Status', 'Submitted At', 'Reviewed By', 'Approved By',
            'Bursary Score',
        ])

        # Rows
        for app in queryset:
            writer.writerow([
                app.application_number,
                str(app.academic_year) if app.academic_year else '',
                app.applicant.get_full_name(),
                app.applicant.id_number,
                str(app.applicant.phone_number),
                app.applicant.email,
                app.applicant.ward,
                app.applicant.location,
                app.get_education_level_display(),
                app.institution.name if app.institution else app.institution_name_other,
                app.course_name,
                app.year_of_study,
                app.total_fees,
                app.amount_requested,
                app.other_support,
                app.approved_amount or '',
                app.family_monthly_income,
                app.number_of_siblings,
                app.siblings_in_school,
                'Yes' if app.is_orphan else 'No',
                'Yes' if app.is_single_parent else 'No',
                'Yes' if app.has_disability else 'No',
                app.get_family_status_display() if app.family_status else '',
                app.get_academic_performance_display() if app.academic_performance else '',
                'Yes' if app.previous_cdf_support else 'No',
                app.get_status_display(),
                app.submitted_at.strftime('%Y-%m-%d %H:%M') if app.submitted_at else '',
                app.reviewed_by.get_full_name() if app.reviewed_by else '',
                app.approved_by.get_full_name() if app.approved_by else '',
                calculate_bursary_score(app),
            ])

        return response


# Disbursement Management
class DisbursementListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List disbursements"""
    model = Disbursement
    template_name = 'bursary/disbursement_list.html'
    context_object_name = 'disbursements'
    paginate_by = 20

    def test_func(self):
        return self.request.user.can_approve_applications

    def get_queryset(self):
        return Disbursement.objects.select_related(
            'application', 'application__applicant', 'processed_by'
        ).order_by('-payment_date')


class DisbursementCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create disbursement record"""
    model = Disbursement
    template_name = 'bursary/disbursement_form.html'
    fields = ['application', 'amount', 'payment_method', 'reference_number',
              'paid_to', 'payment_date', 'receipt_number', 'notes']
    success_url = reverse_lazy('bursary:disbursement_list')

    def test_func(self):
        return self.request.user.can_approve_applications

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get approved applications without disbursements
        context['pending_applications'] = BursaryApplication.objects.filter(
            status='approved'
        ).exclude(
            disbursements__isnull=False
        ).select_related('applicant', 'institution')
        return context

    def form_valid(self, form):
        form.instance.processed_by = self.request.user
        response = super().form_valid(form)

        # Update application status
        application = form.instance.application
        old_status = application.status
        new_status = 'disbursed'
        application.status = new_status
        application.save()

        # Create status log
        ApplicationStatusLog.objects.create(
            application=application,
            previous_status=old_status,
            new_status='disbursed',
            changed_by=self.request.user,
            comment=f'Disbursement of KES {form.instance.amount:,.2f} processed'
        )

        # Send notification
        send_application_status_notification(application, old_status, new_status)

        messages.success(
            self.request,
            f'Disbursement for {application.application_number} recorded successfully.'
        )

        return response


class DisbursementDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """View disbursement details"""
    model = Disbursement
    template_name = 'bursary/disbursement_detail.html'
    context_object_name = 'disbursement'

    def test_func(self):
        return self.request.user.can_review_applications


# Institution Management
class InstitutionListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List institutions"""
    model = Institution
    template_name = 'bursary/institution_list.html'
    context_object_name = 'institutions'
    paginate_by = 50

    def test_func(self):
        return self.request.user.can_review_applications

    def get_queryset(self):
        queryset = Institution.objects.annotate(
            application_count=Count('applications')
        )

        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(county__icontains=search)
            )

        # Filter by type
        inst_type = self.request.GET.get('type')
        if inst_type:
            queryset = queryset.filter(institution_type=inst_type)

        return queryset.order_by('name')


class InstitutionCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Add new institution"""
    model = Institution
    template_name = 'bursary/institution_form.html'
    fields = ['name', 'institution_type', 'county', 'address', 'is_verified']
    success_url = reverse_lazy('bursary:institution_list')

    def test_func(self):
        return self.request.user.can_approve_applications

    def form_valid(self, form):
        messages.success(self.request, 'Institution added successfully.')
        return super().form_valid(form)


class InstitutionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update institution"""
    model = Institution
    template_name = 'bursary/institution_form.html'
    fields = ['name', 'institution_type', 'county', 'address', 'is_verified']
    success_url = reverse_lazy('bursary:institution_list')

    def test_func(self):
        return self.request.user.can_approve_applications

    def form_valid(self, form):
        messages.success(self.request, 'Institution updated successfully.')
        return super().form_valid(form)


# Academic Year Management
class AcademicYearListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List academic years"""
    model = AcademicYear
    template_name = 'bursary/academic_year_list.html'
    context_object_name = 'academic_years'
    ordering = ['-start_date']

    def test_func(self):
        return self.request.user.can_approve_applications


class AcademicYearCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create academic year"""
    model = AcademicYear
    template_name = 'bursary/academic_year_form.html'
    fields = ['year', 'start_date', 'end_date', 'application_deadline', 'is_active']
    success_url = reverse_lazy('bursary:academic_year_list')

    def test_func(self):
        return self.request.user.can_approve_applications

    def form_valid(self, form):
        # If marking as active, deactivate others
        if form.instance.is_active:
            AcademicYear.objects.update(is_active=False)

        messages.success(self.request, 'Academic year created successfully.')
        return super().form_valid(form)


class AcademicYearUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update academic year"""
    model = AcademicYear
    template_name = 'bursary/academic_year_form.html'
    fields = ['year', 'start_date', 'end_date', 'application_deadline', 'is_active']
    success_url = reverse_lazy('bursary:academic_year_list')

    def test_func(self):
        return self.request.user.can_approve_applications

    def form_valid(self, form):
        # If marking as active, deactivate others
        if form.instance.is_active:
            AcademicYear.objects.exclude(pk=form.instance.pk).update(is_active=False)

        messages.success(self.request, 'Academic year updated successfully.')
        return super().form_valid(form)


# API Views for React Frontend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class BursaryApplicationViewSet(viewsets.ModelViewSet):
    """API ViewSet for bursary applications"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.can_review_applications:
            return BursaryApplication.objects.all()
        return BursaryApplication.objects.filter(applicant=user)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit a draft application"""
        application = self.get_object()

        if application.status != 'draft':
            return Response(
                {'error': 'Only draft applications can be submitted'},
                status=status.HTTP_400_BAD_REQUEST
            )

        application.status = 'submitted'
        application.submitted_at = timezone.now()
        application.save()

        # Send notification
        send_application_submitted_notification(request, application)

        return Response({'status': 'submitted'})

    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """Review an application (staff only)"""
        if not request.user.can_review_applications:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        application = self.get_object()
        # Implement review logic

        return Response({'status': 'reviewed'})
        # The following lines appear to be misplaced or a copy-paste error from another view.
        # They are not relevant to the API 'review' action and would cause a NameError for 'context'.
        # context['status_logs'] = self.object.status_logs.all().order_by('-created_at')
        #
        # # Calculate bursary score for reviewers
        # if self.request.user.can_review_applications:
        #     context['bursary_score'] = calculate_bursary_score(self.object)
        #
        # return context


class ApplicationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update application (only for drafts)"""
    model = BursaryApplication
    form_class = BursaryApplicationForm
    template_name = 'bursary/application_form.html'

    def test_func(self):
        application = self.get_object()
        return (
            application.applicant == self.request.user and
            application.is_editable
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # We handle the 'submit_application' in ApplicationSubmitView.
        # This view is purely for updating the draft application details.
        response = super().form_valid(form)
        messages.success(self.request, 'Application updated successfully.')
        return response

    def get_success_url(self):
        # After updating a draft, redirect to document upload
        # if 'save_continue' button was clicked in the form.
        # Otherwise, redirect to application list if 'save_draft' was clicked.
        if hasattr(self, 'object') and self.object and self.object.pk:
            if 'save_draft' in self.request.POST:
                return reverse_lazy('bursary:application_list')
            else:
                return reverse_lazy('bursary:document_upload', kwargs={'pk': self.object.pk})
        else:
            messages.error(self.request, 'An error occurred. Please try again.')
            return reverse_lazy('bursary:application_list')


class ApplicationSubmitView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Submit a draft application"""
    def test_func(self):
        application = get_object_or_404(
            BursaryApplication,
            pk=self.kwargs['pk']
        )
        return (
            application.applicant == self.request.user and
            application.status == 'draft'
        )

    def post(self, request, pk):
        application = get_object_or_404(BursaryApplication, pk=pk)

        # Check declarations
        student_decl = request.POST.get('student_declaration')
        guardian_decl = request.POST.get('guardian_declaration')

        if not student_decl or not guardian_decl:
            messages.error(
                request,
                'You must accept both the Student Declaration and the Parent/Guardian Declaration before submitting.'
            )
            return redirect('bursary:document_upload', pk=pk)

        # Check if required documents are uploaded
        required_docs = ['fee_structure', 'transcript', 'parent_id', 'birth_certificate']

        # Add conditional requirements based on education level
        if application.education_level in ('tvet', 'undergraduate', 'postgraduate'):
            required_docs.extend(['student_id', 'admission_letter'])
        if application.education_level in ('secondary', 'tvet', 'undergraduate', 'postgraduate'):
            required_docs.append('school_id')

        # Add conditional requirements based on circumstances
        if application.is_orphan:
            required_docs.append('death_certificate')
        if application.has_disability:
            required_docs.append('disability_cert')

        uploaded_types = list(application.documents.values_list('document_type', flat=True))

        missing_docs = [doc for doc in required_docs if doc not in uploaded_types]

        if missing_docs:
            # Build a readable list of missing document names
            doc_type_labels = dict(ApplicationDocument.DOCUMENT_TYPES)
            missing_names = [doc_type_labels.get(d, d).split('(')[0].strip().lstrip('0123456789. ') for d in missing_docs]
            messages.error(
                request,
                f'Please upload the following required documents before submitting: {", ".join(missing_names)}'
            )
            return redirect('bursary:document_upload', pk=pk)

        # Record declarations and submit
        application.student_declaration_accepted = True
        application.guardian_declaration_accepted = True
        application.declaration_accepted_at = timezone.now()

        # Handle optional signature uploads with strict validation
        SIG_MAX_SIZE = 500 * 1024  # 500KB
        SIG_MIN_W, SIG_MAX_W = 200, 800
        SIG_MIN_H, SIG_MAX_H = 50, 300
        SIG_ALLOWED_TYPES = ['image/png', 'image/jpeg', 'image/jpg']

        def validate_signature(file_obj, label):
            """Validate signature image dimensions and size. Returns error string or None."""
            if file_obj.size > SIG_MAX_SIZE:
                return f'{label}: File size is {file_obj.size // 1024}KB — maximum is 500KB.'
            if file_obj.content_type not in SIG_ALLOWED_TYPES:
                return f'{label}: Only PNG and JPG images are accepted.'
            try:
                from PIL import Image
                img = Image.open(file_obj)
                w, h = img.size
                file_obj.seek(0)  # Reset file pointer after reading
                if w < SIG_MIN_W or w > SIG_MAX_W:
                    return f'{label}: Width is {w}px — must be between {SIG_MIN_W}–{SIG_MAX_W}px.'
                if h < SIG_MIN_H or h > SIG_MAX_H:
                    return f'{label}: Height is {h}px — must be between {SIG_MIN_H}–{SIG_MAX_H}px.'
            except Exception:
                return f'{label}: Could not read image. Please upload a valid PNG or JPG.'
            return None

        sig_errors = []
        if 'student_signature' in request.FILES:
            err = validate_signature(request.FILES['student_signature'], "Student's signature")
            if err:
                sig_errors.append(err)
            else:
                application.student_signature = request.FILES['student_signature']
        if 'guardian_signature' in request.FILES:
            err = validate_signature(request.FILES['guardian_signature'], "Guardian's signature")
            if err:
                sig_errors.append(err)
            else:
                application.guardian_signature = request.FILES['guardian_signature']

        if sig_errors:
            for e in sig_errors:
                messages.error(request, e)
            return redirect('bursary:document_upload', pk=pk)

        application.status = 'submitted'
        application.submitted_at = timezone.now()
        application.save()

        # Create status log
        ApplicationStatusLog.objects.create(
            application=application,
            previous_status='draft',
            new_status='submitted',
            changed_by=request.user,
            comment='Application submitted by applicant'
        )

        # Send notification
        send_application_submitted_notification(request, application)

        messages.success(
            request,
            'Application submitted successfully! You will be notified of the outcome.'
        )
        return redirect('bursary:application_detail', pk=pk)


class ApplicationDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete application (only drafts)"""
    model = BursaryApplication
    template_name = 'bursary/application_confirm_delete.html'
    success_url = reverse_lazy('bursary:application_list')

    def test_func(self):
        application = self.get_object()
        return (
            application.applicant == self.request.user and
            application.status == 'draft'
        )

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Application deleted successfully.')
        return super().delete(request, *args, **kwargs)


# Document Management Views
class DocumentListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List documents for an application"""
    model = ApplicationDocument
    template_name = 'bursary/document_list.html'
    context_object_name = 'documents'

    def test_func(self):
        application = get_object_or_404(
            BursaryApplication,
            pk=self.kwargs['pk']
        )
        return (
            application.applicant == self.request.user or
            self.request.user.can_review_applications
        )

    def get_queryset(self):
        return ApplicationDocument.objects.filter(
            application_id=self.kwargs['pk']
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['application'] = get_object_or_404(
            BursaryApplication,
            pk=self.kwargs['pk']
        )
        return context


class DocumentUploadView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Upload documents for application"""
    model = ApplicationDocument
    form_class = ApplicationDocumentForm
    template_name = 'bursary/document_upload.html'

    def test_func(self):
        application = get_object_or_404(
            BursaryApplication,
            pk=self.kwargs['pk']
        )
        return (
            application.applicant == self.request.user and
            application.is_editable
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        application = get_object_or_404(
            BursaryApplication,
            pk=self.kwargs['pk']
        )
        context['application'] = application
        documents = ApplicationDocument.objects.filter(
            application_id=self.kwargs['pk']
        )
        context['documents'] = documents

        # Build a simple list of uploaded document type keys for easy checking
        context['uploaded_types'] = list(documents.values_list('document_type', flat=True))

        # Required documents (mandatory for ALL applicants)
        context['required_docs'] = [
            ('fee_structure', 'Current Fees Structure'),
            ('transcript', "Student's Transcript / Report Form"),
            ('parent_id', "Parent's / Guardian's National ID Copy"),
            ('birth_certificate', 'Birth Certificate Copy'),
        ]

        # Conditionally required based on education level
        conditional_docs = []
        if application.education_level in ('tvet', 'undergraduate', 'postgraduate'):
            conditional_docs.append(('student_id', "Student's National ID Copy"))
            conditional_docs.append(('admission_letter', 'Admission Letter'))
        if application.education_level in ('secondary', 'tvet', 'undergraduate', 'postgraduate'):
            conditional_docs.append(('school_id', 'Secondary / College / University ID Card Copy'))
        context['conditional_docs'] = conditional_docs

        # Optional documents based on circumstances
        optional_docs = []
        if application.is_orphan:
            optional_docs.append(('death_certificate', 'Death Certificate / Burial Permit'))
        if application.has_disability:
            optional_docs.append(('disability_cert', 'Disability Certificate'))
        if getattr(application, 'has_chronic_illness', False):
            optional_docs.append(('medical_report', 'Medical Report / Chronic Illness Evidence'))
        optional_docs.append(('chief_letter', 'Verification Letter from Area Chief'))
        optional_docs.append(('recommendation_letter', 'Recommendation Letter'))
        context['optional_docs'] = optional_docs

        return context

    def form_valid(self, form):
        form.instance.application_id = self.kwargs['pk']
        messages.success(self.request, 'Document uploaded successfully.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('bursary:document_upload', kwargs={'pk': self.kwargs['pk']})


class DocumentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete uploaded document"""
    model = ApplicationDocument

    def test_func(self):
        document = self.get_object()
        return (
            document.application.applicant == self.request.user and
            document.application.is_editable
        )

    def delete(self, request, *args, **kwargs):
        document = self.get_object()
        application_id = document.application.id

        # Delete the file from storage
        if document.file:
            document.file.delete()

        messages.success(request, 'Document deleted successfully.')
        response = super().delete(request, *args, **kwargs)

        return redirect('bursary:document_upload', pk=application_id)


class DocumentDownloadView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Download document (for staff)"""
    def test_func(self):
        return self.request.user.can_review_applications

    def get(self, request, pk, doc_id):
        document = get_object_or_404(ApplicationDocument, pk=doc_id)

        if document.application.id != pk:
            raise Http404

        # Serve the file
        response = HttpResponse(
            document.file.read(),
            content_type='application/octet-stream'
        )
        response['Content-Disposition'] = f'attachment; filename="{document.file.name}"'
        return response


# Application Status Views
class ApplicationStatusView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Track application status"""
    model = BursaryApplication
    template_name = 'bursary/application_status.html'
    context_object_name = 'application'

    def test_func(self):
        application = self.get_object()
        return (
            application.applicant == self.request.user or
            self.request.user.can_review_applications
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_logs'] = self.object.status_logs.all().order_by('created_at')
        return context


# Admin/Staff Views
class AdminApplicationListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List applications for review (admin)"""
    model = BursaryApplication
    template_name = 'bursary/admin_application_list.html'
    context_object_name = 'applications'
    paginate_by = 20

    def test_func(self):
        return self.request.user.can_review_applications

    def get_queryset(self):
        queryset = BursaryApplication.objects.select_related(
            'applicant', 'academic_year', 'institution'
        ).exclude(status='draft')

        # Apply filters
        filter_form = ApplicationFilterForm(self.request.GET)

        if filter_form.is_valid():
            status = filter_form.cleaned_data.get('status')
            if status:
                queryset = queryset.filter(status=status)

            education_level = filter_form.cleaned_data.get('education_level')
            if education_level:
                queryset = queryset.filter(education_level=education_level)

            search = filter_form.cleaned_data.get('search')
            if search:
                queryset = queryset.filter(
                    Q(application_number__icontains=search) |
                    Q(applicant__first_name__icontains=search) |
                    Q(applicant__last_name__icontains=search) |
                    Q(applicant__id_number__icontains=search)
                )

            date_from = filter_form.cleaned_data.get('date_from')
            if date_from:
                queryset = queryset.filter(submitted_at__date__gte=date_from)

            date_to = filter_form.cleaned_data.get('date_to')
            if date_to:
                queryset = queryset.filter(submitted_at__date__lte=date_to)

        # Add bursary scores
        for app in queryset:
            app.bursary_score = calculate_bursary_score(app)

        return queryset.order_by('-submitted_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = ApplicationFilterForm(self.request.GET)

        # Statistics
        queryset = self.get_queryset()
        context['total_count'] = queryset.count()
        context['total_requested'] = queryset.aggregate(
            Sum('amount_requested')
        )['amount_requested__sum'] or 0

        return context


class AdminApplicationDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Admin view for application details"""
    model = BursaryApplication
    template_name = 'bursary/application_detail.html'
    context_object_name = 'application'

    def test_func(self):
        return self.request.user.can_review_applications

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['documents'] = self.object.documents.all()
        context['status_logs'] = self.object.status_logs.all().order_by('-created_at')
        # Calculate bursary score for reviewers
        if self.request.user.can_review_applications:
            context['bursary_score'] = calculate_bursary_score(self.object)
        return context


from django.http import JsonResponse

class FilterInstitutionsView(LoginRequiredMixin, View):
    """AJAX view to filter institutions based on education level"""

    def get(self, request, *args, **kwargs):
        try:
            education_level = request.GET.get('education_level', '')

            print(f"\n=== FilterInstitutionsView Debug ===")
            print(f"Education level received: {education_level}")

            # Map education levels to institution types
            type_mapping = {
                'primary': 'primary',
                'secondary': 'secondary',
                'tvet': 'tvet',
                'undergraduate': 'university',
                'postgraduate': 'university',
                # Add this line to handle direct university type
                'university': 'university',  # Handle when type is passed directly
            }

            institution_type = type_mapping.get(education_level)
            print(f"Mapped institution type: {institution_type}")

            # Query filtered institutions
            if institution_type:
                institutions = Institution.objects.filter(
                    institution_type=institution_type,
                    is_verified=True
                ).order_by('name')
            else:
                # If no type mapping, return all verified institutions
                institutions = Institution.objects.filter(
                    is_verified=True
                ).order_by('name')

            print(f"Found {institutions.count()} institutions")

            # Build response data
            data = {
                'institutions': [
                    {
                        'id': inst.id,
                        'name': inst.name,
                        'type': inst.institution_type
                    }
                    for inst in institutions
                ],
                'debug': {
                    'education_level': education_level,
                    'institution_type': institution_type,
                    'total_count': institutions.count(),
                }
            }

            return JsonResponse(data)

        except Exception as e:
            print(f"Error in FilterInstitutionsView: {str(e)}")
            import traceback
            traceback.print_exc()

            return JsonResponse({
                'error': str(e),
                'institutions': []
            }, status=500)

class EmailVerificationView(View):
    """Handle email verification"""

    def get(self, request, uidb64, token):
        user = EmailVerificationService.verify_token(uidb64, token)

        if user:
            # Mark user as verified (assuming you have an is_verified field)
            if hasattr(user, 'is_verified'):
                user.is_verified = True
                user.save()

            # Activate user account if it's not active
            if not user.is_active:
                user.is_active = True
                user.save()

            # Log the user in
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')

            messages.success(request, 'Your email has been verified successfully! You can now proceed with your application.')

            # Check if user has a pending application
            if hasattr(user, 'bursaryapplication_set'):
                pending_apps = user.bursaryapplication_set.filter(status='draft')
                if pending_apps.exists():
                    return redirect('bursary:application_detail', pk=pending_apps.first().pk)

            return redirect('bursary:application_create')
        else:
            messages.error(request, 'The verification link is invalid or has expired. Please request a new one.')
            return redirect('login')


class ResendVerificationEmailView(View):
    """Resend verification email"""

    def post(self, request):
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to resend verification email.')
            return redirect('login')

        user = request.user

        # Check if already verified
        if hasattr(user, 'is_verified') and user.is_verified:
            messages.info(request, 'Your email is already verified.')
            return redirect('bursary:application_create')

        # Send verification email
        if EmailVerificationService.send_verification_email(request, user):
            messages.success(request, 'Verification email sent! Please check your inbox.')
        else:
            messages.error(request, 'Failed to send verification email. Please try again later.')

        return redirect(request.META.get('HTTP_REFERER', 'home'))