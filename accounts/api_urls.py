from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)
from . import views

urlpatterns = [
    # JWT Token endpoints
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # User management
    path('register/', views.RegisterAPIView.as_view(), name='api_register'),
    path('profile/', views.ProfileAPIView.as_view(), name='api_profile'),
    path('verify-email/', views.VerifyEmailAPIView.as_view(), name='api_verify_email'),
    path('resend-verification/', views.ResendVerificationCodeAPIView.as_view(), name='api_resend_verification'),
    
    # Session keep-alive
    path('keep-alive/', views.keep_alive_view, name='api_keep_alive'),
]