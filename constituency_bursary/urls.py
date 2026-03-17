"""
URL configuration for constituency_bursary project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # Home page
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    
    # Authentication URLs
    path('accounts/', include('accounts.urls', namespace='accounts')),
    
    # Bursary application URLs
    path('bursary/', include('bursary.urls', namespace='bursary')),
    
    # API endpoints for React frontend
    path('api/auth/', include('accounts.api_urls')),
    path('api/bursary/', include('bursary.api_urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Debug toolbar
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

# Custom error pages
handler403 = 'constituency_bursary.views.custom_403'
handler404 = 'constituency_bursary.views.custom_404'
handler500 = 'constituency_bursary.views.custom_500'