from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView, FormView, View
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta


from .forms import UserRegistrationForm, UserProfileForm, EmailVerificationForm, CustomAuthenticationForm
from .models import User, UserProfile, VerificationCode
from bursary.utils import send_verification_code
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSerializer, RegisterSerializer, VerificationSerializer


class CustomLoginView(LoginView):
    """Custom login view with phone number support"""
    template_name = 'accounts/login.html'
    authentication_form = CustomAuthenticationForm
    redirect_authenticated_user = True
    
    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        
        # Redirect based on user role
        if self.request.user.can_review_applications:
            return reverse_lazy('bursary:admin_application_list')
        return reverse_lazy('bursary:dashboard')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Welcome back, {self.request.user.get_full_name()}!")
        return response


class RegisterView(CreateView):
    """User registration view"""
    model = User
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:verify_email')
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('bursary:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Log the user in
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')
        user = authenticate(username=username, password=password)
        login(self.request, user)
        
        # Send verification code with request context
        send_verification_code(user, self.request)  # Pass request here
        
        messages.success(
            self.request, 
            'Registration successful! Please check your email for the verification code.'
        )
        return response


class EmailVerificationView(LoginRequiredMixin, FormView):
    """Email verification view"""
    template_name = 'accounts/verify_email.html'
    form_class = EmailVerificationForm
    success_url = reverse_lazy('bursary:dashboard')
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_verified:
            messages.info(request, 'Your Email is already verified.')
            return redirect('bursary:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['phone_number'] = self.request.user.phone_number
        return context
    
    def form_valid(self, form):
        code = form.cleaned_data.get('verification_code')
        
        # Check for valid verification code
        verification = VerificationCode.objects.filter(
            user=self.request.user,
            code=code,
            is_used=False,
            expires_at__gt=timezone.now()
        ).first()
        
        if verification:
            # Mark user as verified
            self.request.user.is_verified = True
            self.request.user.save()
            
            # Mark code as used
            verification.is_used = True
            verification.save()
            
            messages.success(
                self.request, 
                'Email address verified successfully! You can now submit bursary applications.'
            )
            return super().form_valid(form)
        else:
            messages.error(
                self.request, 
                'Invalid or expired verification code. Please try again.'
            )
            return self.form_invalid(form)


class ResendVerificationCodeView(LoginRequiredMixin, View):
    """Resend verification code"""
    def post(self, request, *args, **kwargs):
        if request.user.is_verified:
            return JsonResponse({
                'status': 'error',
                'message': 'Email already verified.'
            })
        
        # Check for recent codes
        recent_code = VerificationCode.objects.filter(
            user=request.user,
            created_at__gt=timezone.now() - timedelta(minutes=2)
        ).exists()
        
        if recent_code:
            return JsonResponse({
                'status': 'error',
                'message': 'Please wait 2 minutes before requesting a new code.'
            })
        
        # Send new code with request context
        try:
            send_verification_code(request.user, request)  # Pass request here
            return JsonResponse({
                'status': 'success',
                'message': 'Verification code sent to your email successfully.'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': 'Failed to send verification code. Please try again.'
            })


class ProfileView(LoginRequiredMixin, DetailView):
    """User profile view"""
    model = User
    template_name = 'accounts/profile.html'
    context_object_name = 'profile_user'
    
    def get_object(self):
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get user's applications
        from bursary.models import BursaryApplication
        applications = BursaryApplication.objects.filter(
            applicant=self.request.user
        ).order_by('-created_at')
        
        # Add applications to context (limit to 5 most recent)
        context['applications'] = applications[:5]
        
        # Add approved applications count
        context['approved_applications'] = applications.filter(status='approved').count()
        
        # Get profile completion percentage
        profile = self.request.user.profile
        completed_fields = 0
        total_fields = 8  # Adjust based on your profile fields
        
        if profile.gender:
            completed_fields += 1
        if profile.guardian_name:
            completed_fields += 1
        if profile.guardian_phone:
            completed_fields += 1
        if profile.guardian_relationship:
            completed_fields += 1
        if profile.emergency_contact_name:
            completed_fields += 1
        if profile.emergency_contact_phone:
            completed_fields += 1
        if profile.id_card_front:
            completed_fields += 1
        if profile.id_card_back:
            completed_fields += 1
        
        context['profile_completion'] = (completed_fields / total_fields) * 100
        
        return context

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Update user profile"""
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self):
        return self.request.user.profile
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # User form for basic info
        from django import forms
        
        class UserBasicInfoForm(forms.ModelForm):
            class Meta:
                model = User
                fields = ['first_name', 'last_name', 'email', 'date_of_birth',
                         'ward', 'sub_county', 'location', 'sub_location', 'village']
                widgets = {
                    'first_name': forms.TextInput(attrs={'class': 'form-control'}),
                    'last_name': forms.TextInput(attrs={'class': 'form-control'}),
                    'email': forms.EmailInput(attrs={'class': 'form-control'}),
                    'date_of_birth': forms.DateInput(attrs={
                        'class': 'form-control',
                        'type': 'date'
                    }),
                    'ward': forms.TextInput(attrs={'class': 'form-control'}),
                    'sub_county': forms.TextInput(attrs={'class': 'form-control'}),
                    'location': forms.TextInput(attrs={'class': 'form-control'}),
                    'sub_location': forms.TextInput(attrs={'class': 'form-control'}),
                    'village': forms.TextInput(attrs={'class': 'form-control'}),
                }
        
        if self.request.method == 'POST':
            context['user_form'] = UserBasicInfoForm(
                self.request.POST, 
                instance=self.request.user
            )
        else:
            context['user_form'] = UserBasicInfoForm(instance=self.request.user)
        
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        user_form = context['user_form']
        
        if user_form.is_valid():
            user_form.save()
            messages.success(self.request, 'Profile updated successfully!')
            return super().form_valid(form)
        else:
            return self.form_invalid(form)


@login_required
def keep_alive_view(request):
    """Keep session alive for AJAX calls"""
    return JsonResponse({'status': 'ok'})


# API Views for React Frontend (if needed)
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken


class RegisterAPIView(generics.CreateAPIView):
    """API endpoint for user registration"""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = (AllowAny,)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Send verification email
        send_verification_code(user, request)
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'Registration successful. Please check your email for verification code.'
        }, status=status.HTTP_201_CREATED)



class ProfileAPIView(generics.RetrieveUpdateAPIView):
    """API endpoint for user profile"""
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_object(self):
        return self.request.user


class VerifyEmailAPIView(APIView):
    """API endpoint for email verification"""
    permission_classes = (IsAuthenticated,)
    serializer_class = VerificationSerializer
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        code = serializer.validated_data['code']
        
        verification = VerificationCode.objects.filter(
            user=request.user,
            code=code,
            is_used=False,
            expires_at__gt=timezone.now()
        ).first()
        
        if verification:
            request.user.is_verified = True
            request.user.save()
            
            verification.is_used = True
            verification.save()
            
            return Response(
                {'message': 'Email verified successfully'},
                status=status.HTTP_200_OK
            )
        
        return Response(
            {'error': 'Invalid or expired verification code'},
            status=status.HTTP_400_BAD_REQUEST
        )


class ResendVerificationCodeAPIView(APIView):
    """API endpoint to resend verification code"""
    permission_classes = (IsAuthenticated,)
    
    def post(self, request):
        if request.user.is_verified:
            return Response({
                'error': 'Email already verified'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check for recent codes
        recent_code = VerificationCode.objects.filter(
            user=request.user,
            created_at__gt=timezone.now() - timedelta(minutes=2)
        ).exists()
        
        if recent_code:
            return Response({
                'error': 'Please wait 2 minutes before requesting a new code'
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Send new code
        try:
            send_verification_code(request.user, request)
            return Response({
                'message': 'Verification code sent to your email successfully'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': 'Failed to send verification code. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)