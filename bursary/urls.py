from django.urls import path
from . import views
from .views import FilterInstitutionsView
from .views import EmailVerificationView, ResendVerificationEmailView

app_name = 'bursary'

urlpatterns = [
    # Dashboard (different view based on user role)
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('ajax/filter-institutions/', FilterInstitutionsView.as_view(), name='filter_institutions'),
    # path('ajax/test-institutions/', views.test_institutions_ajax, name='test_institutions'),  # Test endpoint
    
    # Application management for applicants
    path('applications/', views.ApplicationListView.as_view(), name='application_list'),
    path('applications/new/', views.ApplicationCreateView.as_view(), name='application_create'),
    path('applications/<int:pk>/', views.ApplicationDetailView.as_view(), name='application_detail'),
    path('applications/<int:pk>/edit/', views.ApplicationUpdateView.as_view(), name='application_update'),
    path('applications/<int:pk>/submit/', views.ApplicationSubmitView.as_view(), name='application_submit'),
    path('applications/<int:pk>/delete/', views.ApplicationDeleteView.as_view(), name='application_delete'),
    
    # Document management
    path('applications/<int:pk>/documents/', views.DocumentListView.as_view(), name='document_list'),
    path('applications/<int:pk>/documents/add/', views.DocumentUploadView.as_view(), name='document_upload'),
    path('documents/<int:pk>/delete/', views.DocumentDeleteView.as_view(), name='document_delete'),
    
    # Application status tracking
    path('applications/<int:pk>/status/', views.ApplicationStatusView.as_view(), name='application_status'),
    
    # Admin/Staff views
    path('admin/applications/', views.AdminApplicationListView.as_view(), name='admin_application_list'),
    path('admin/applications/<int:pk>/', views.AdminApplicationDetailView.as_view(), name='admin_application_detail'),
    path('admin/applications/<int:pk>/review/', views.ApplicationReviewView.as_view(), name='application_review'),
    path('admin/applications/<int:pk>/documents/<int:doc_id>/', views.DocumentDownloadView.as_view(), name='document_download'),
    
    # Reports and analytics
    path('admin/reports/', views.ReportsView.as_view(), name='reports'),
    path('admin/reports/export/', views.ExportApplicationsView.as_view(), name='export_applications'),
    
    # Disbursement management
    path('admin/disbursements/', views.DisbursementListView.as_view(), name='disbursement_list'),
    path('admin/disbursements/new/', views.DisbursementCreateView.as_view(), name='disbursement_create'),
    path('admin/disbursements/<int:pk>/', views.DisbursementDetailView.as_view(), name='disbursement_detail'),
    
    # Institution management
    path('admin/institutions/', views.InstitutionListView.as_view(), name='institution_list'),
    path('admin/institutions/add/', views.InstitutionCreateView.as_view(), name='institution_create'),
    path('admin/institutions/<int:pk>/edit/', views.InstitutionUpdateView.as_view(), name='institution_update'),
    
    # Academic year management
    path('admin/academic-years/', views.AcademicYearListView.as_view(), name='academic_year_list'),
    path('admin/academic-years/add/', views.AcademicYearCreateView.as_view(), name='academic_year_create'),
    path('admin/academic-years/<int:pk>/edit/', views.AcademicYearUpdateView.as_view(), name='academic_year_update'),

    # Email verification
    path('verify-email/<uidb64>/<token>/', 
         EmailVerificationView.as_view(), 
         name='verify-email'),
    
    path('resend-verification/', 
         ResendVerificationEmailView.as_view(), 
         name='resend-verification'),
]