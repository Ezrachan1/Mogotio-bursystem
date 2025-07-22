from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'applications', views.BursaryApplicationViewSet, basename='application')

urlpatterns = [
    path('', include(router.urls)),
    
    # Additional API endpoints
    path('dashboard-stats/', views.DashboardView.as_view(), name='api_dashboard_stats'),
    path('institutions/', views.InstitutionListView.as_view(), name='api_institutions'),
    path('academic-years/', views.AcademicYearListView.as_view(), name='api_academic_years'),
    path('reports/', views.ReportsView.as_view(), name='api_reports'),
]