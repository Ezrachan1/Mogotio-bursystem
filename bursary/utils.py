# bursary/utils.py
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from django.contrib.auth import get_user_model
# Temporary debug - remove after fixing
print("Loading bursary/utils.py...")

User = get_user_model()


def send_verification_code(request, user, application=None):
    """Send verification code to user"""
    try:
        return EmailVerificationService.send_verification_email(request, user, application)
    except Exception as e:
        print(f"Error sending verification email: {e}")
        if settings.DEBUG:
            token, uid = EmailVerificationService.generate_verification_token(user)
            verification_url = request.build_absolute_uri(f'/bursary/verify-email/{uid}/{token}/')
            print(f"Verification URL for {user.email}: {verification_url}")
        return False


def send_application_submitted_notification(request, application):
    """Send notification when application is submitted"""
    try:
        user = application.user
        return EmailVerificationService.send_application_confirmation_email(request, user, application)
    except Exception as e:
        print(f"Error sending application notification: {e}")
        if settings.DEBUG:
            print(f"Application {application.application_number} submitted by {getattr(application, 'user', 'Unknown')}")
        return False


def send_application_status_notification(application, old_status, new_status):
    """Send notification when application status changes"""
    return send_application_status_update(application, old_status, new_status)


def send_application_status_update(application, old_status, new_status):
    """Send notification when application status changes"""
    if settings.DEBUG:
        print(f"Application {application.application_number} status changed from {old_status} to {new_status}")
    
    try:
        user = application.user
        subject = f'Bursary Application Status Update - {application.application_number}'
        message = f"""
Dear {user.first_name or 'Applicant'},

Your bursary application status has been updated.

Reference Number: {application.application_number}
Previous Status: {old_status}
New Status: {new_status}

Thank you,
Constituency Bursary System
        """
        
        if hasattr(settings, 'EMAIL_HOST_USER') and settings.EMAIL_HOST_USER:
            from django.core.mail import send_mail
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        return True
    except Exception as e:
        print(f"Error sending status update: {e}")
        return False


def send_password_reset_email(request, user, token):
    """Send password reset email"""
    reset_url = request.build_absolute_uri(f'/accounts/reset-password/{token}/')
    
    if settings.DEBUG:
        print(f"Password reset URL for {user.email}: {reset_url}")
    
    try:
        subject = 'Password Reset - Constituency Bursary System'
        message = f"""
Hello {user.first_name or 'there'},

You requested a password reset. Click the link below to reset your password:

{reset_url}

This link will expire in 24 hours.

If you didn't request this, please ignore this email.

Thank you,
Constituency Bursary System
        """
        
        if hasattr(settings, 'EMAIL_HOST_USER') and settings.EMAIL_HOST_USER:
            from django.core.mail import send_mail
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        return True
    except Exception as e:
        print(f"Error sending password reset email: {e}")
        return False


def send_application_approved_notification(application):
    """Send notification when application is approved"""
    if settings.DEBUG:
        print(f"Application {application.application_number} has been approved!")
    
    try:
        user = application.user
        subject = f'Bursary Application Approved - {application.application_number}'
        message = f"""
Dear {user.first_name or 'Applicant'},

Congratulations! Your bursary application has been approved.

Reference Number: {application.application_number}
Amount Approved: KES {getattr(application, 'amount_approved', application.amount_requested)}

Further instructions will be sent to you shortly.

Thank you,
Constituency Bursary System
        """
        
        if hasattr(settings, 'EMAIL_HOST_USER') and settings.EMAIL_HOST_USER:
            from django.core.mail import send_mail
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        return True
    except Exception as e:
        print(f"Error sending approval notification: {e}")
        return False


def send_application_rejected_notification(application, reason=None):
    """Send notification when application is rejected"""
    if settings.DEBUG:
        print(f"Application {application.application_number} has been rejected")
    
    try:
        user = application.user
        subject = f'Bursary Application Update - {application.application_number}'
        message = f"""
Dear {user.first_name or 'Applicant'},

We regret to inform you that your bursary application has not been approved at this time.

Reference Number: {application.application_number}
{f'Reason: {reason}' if reason else ''}

You may be eligible to apply again in the next cycle.

Thank you,
Constituency Bursary System
        """
        
        if hasattr(settings, 'EMAIL_HOST_USER') and settings.EMAIL_HOST_USER:
            from django.core.mail import send_mail
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        return True
    except Exception as e:
        print(f"Error sending rejection notification: {e}")
        return False


def send_disbursement_notification(application, amount, date):
    """Send notification when funds are disbursed"""
    if settings.DEBUG:
        print(f"Disbursement for {application.application_number}: KES {amount} on {date}")
    
    try:
        user = application.user
        subject = f'Bursary Funds Disbursed - {application.application_number}'
        message = f"""
Dear {user.first_name or 'Applicant'},

Your bursary funds have been disbursed.

Reference Number: {application.application_number}
Amount Disbursed: KES {amount}
Date: {date}

The funds have been sent to your institution.

Thank you,
Constituency Bursary System
        """
        
        if hasattr(settings, 'EMAIL_HOST_USER') and settings.EMAIL_HOST_USER:
            from django.core.mail import send_mail
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        return True
    except Exception as e:
        print(f"Error sending disbursement notification: {e}")
        return False


class EmailVerificationService:
    """Service for handling email verification"""
    
    @staticmethod
    def generate_verification_token(user):
        """Generate verification token and uid for user"""
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        return token, uid
    
    @staticmethod
    def verify_token(uidb64, token):
        """Verify the token and return user if valid"""
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return None
        
        if default_token_generator.check_token(user, token):
            return user
        return None
    
    @staticmethod
    def send_verification_email(request, user, application=None):
        """Send verification email to user"""
        token, uid = EmailVerificationService.generate_verification_token(user)
        
        # Build verification URL
        verification_url = request.build_absolute_uri(
            f'/bursary/verify-email/{uid}/{token}/'
        )
        
        # Context for email template
        context = {
            'user': user,
            'verification_url': verification_url,
            'application': application,
            'site_name': 'Constituency Bursary System',
        }
        
        # Check if templates exist, otherwise use simple text email
        try:
            # Try to render HTML template
            html_content = render_to_string('bursary/emails/verify_email.html', context)
            text_content = strip_tags(html_content)
        except:
            # Fallback to simple text if template doesn't exist
            text_content = f"""
Hello {user.first_name or 'there'},

Please verify your email address by clicking the link below:

{verification_url}

This link will expire in 24 hours.

Thank you,
Constituency Bursary System
            """
            html_content = None
        
        # Create email
        subject = 'Verify Your Email - Constituency Bursary Application'
        from_email = settings.DEFAULT_FROM_EMAIL or 'noreply@example.com'
        to_email = user.email
        
        # For development without email configured
        if settings.DEBUG and not hasattr(settings, 'EMAIL_HOST_USER'):
            print(f"\n{'='*50}")
            print(f"VERIFICATION EMAIL (Debug Mode)")
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print(f"Verification URL: {verification_url}")
            print(f"{'='*50}\n")
            return True
        
        # Send actual email
        try:
            if html_content:
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=from_email,
                    to=[to_email]
                )
                email.attach_alternative(html_content, "text/html")
            else:
                # Send plain text email
                from django.core.mail import send_mail
                send_mail(
                    subject=subject,
                    message=text_content,
                    from_email=from_email,
                    recipient_list=[to_email],
                    fail_silently=False,
                )
            
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            if settings.DEBUG:
                print(f"Verification URL: {verification_url}")
            return False
    
    @staticmethod
    def send_application_confirmation_email(request, user, application):
        """Send confirmation email after successful application"""
        context = {
            'user': user,
            'application': application,
            'site_name': 'Constituency Bursary System',
        }
        
        # Check if templates exist
        try:
            html_content = render_to_string('bursary/emails/application_confirmation.html', context)
            text_content = strip_tags(html_content)
        except:
            # Fallback text
            text_content = f"""
Dear {user.first_name or 'Applicant'},

Your bursary application has been successfully submitted.

Reference Number: {application.application_number}
Institution: {application.institution_name}
Amount Requested: KES {application.amount_requested}

You will receive updates via email as your application progresses.

Thank you,
Constituency Bursary System
            """
            html_content = None
        
        # Create email
        subject = f'Bursary Application Received - Reference: {application.application_number}'
        from_email = settings.DEFAULT_FROM_EMAIL or 'noreply@example.com'
        to_email = user.email
        
        # For development
        if settings.DEBUG and not hasattr(settings, 'EMAIL_HOST_USER'):
            print(f"\n{'='*50}")
            print(f"CONFIRMATION EMAIL (Debug Mode)")
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print(f"Reference: {application.application_number}")
            print(f"{'='*50}\n")
            return True
        
        # Send email
        try:
            if html_content:
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=from_email,
                    to=[to_email]
                )
                email.attach_alternative(html_content, "text/html")
                email.send(fail_silently=False)
            else:
                from django.core.mail import send_mail
                send_mail(
                    subject=subject,
                    message=text_content,
                    from_email=from_email,
                    recipient_list=[to_email],
                    fail_silently=False,
                )
            return True
        except Exception as e:
            print(f"Error sending confirmation email: {e}")
            return False

def calculate_bursary_score(application):
    """
    Calculate a score for the bursary application based on various criteria.
    Higher score = higher priority for funding.
    
    Scoring criteria (example):
    - Family income (lower income = higher score)
    - Academic performance
    - Special circumstances (orphan, disability, etc.)
    - Previous funding received
    """
    score = 0
    
    try:
        # Family income scoring (inverse relationship)
        # Lower income gets higher score
        family_income = getattr(application, 'family_income', 0)
        if family_income == 0:
            score += 100  # No income
        elif family_income < 10000:
            score += 80
        elif family_income < 20000:
            score += 60
        elif family_income < 30000:
            score += 40
        elif family_income < 50000:
            score += 20
        else:
            score += 10
        
        # Academic performance scoring
        # Assuming grades are stored as a percentage or GPA
        academic_score = getattr(application, 'academic_score', 0)
        if academic_score >= 80:
            score += 50  # Excellent
        elif academic_score >= 70:
            score += 40  # Good
        elif academic_score >= 60:
            score += 30  # Average
        elif academic_score >= 50:
            score += 20  # Below average
        else:
            score += 10
        
        # Special circumstances
        if getattr(application, 'is_orphan', False):
            score += 30
        
        if getattr(application, 'has_disability', False):
            score += 25
        
        if getattr(application, 'is_single_parent_family', False):
            score += 20
        
        # Year of study (higher years might get priority)
        year_of_study = getattr(application, 'year_of_study', 1)
        score += year_of_study * 5
        
        # Previous funding (those who haven't received before get priority)
        if not getattr(application, 'received_bursary_before', False):
            score += 15
        
        # Amount requested vs amount available
        # Smaller requests might be easier to fulfill
        amount_requested = getattr(application, 'amount_requested', 0)
        if amount_requested < 20000:
            score += 10
        elif amount_requested < 30000:
            score += 5
        
        if settings.DEBUG:
            print(f"Calculated score for application {getattr(application, 'reference_number', 'N/A')}: {score}")
        
        return score
        
    except Exception as e:
        print(f"Error calculating bursary score: {e}")
        return 0


def get_bursary_statistics():
    """
    Get statistics about bursary applications.
    Useful for dashboard and reporting.
    """
    # This is a placeholder - implement based on your models
    stats = {
        'total_applications': 0,
        'pending_applications': 0,
        'approved_applications': 0,
        'rejected_applications': 0,
        'total_amount_requested': 0,
        'total_amount_approved': 0,
        'average_score': 0,
    }
    
    if settings.DEBUG:
        print("Bursary statistics requested")
    
    return stats


def validate_application_documents(application):
    """
    Validate that all required documents are uploaded.
    """
    required_documents = [
        'national_id',
        'admission_letter',
        'fee_structure',
        'parent_id',
        # Add more as per your requirements
    ]
    
    missing_documents = []
    
    for doc_type in required_documents:
        if not hasattr(application, f'{doc_type}_document') or not getattr(application, f'{doc_type}_document'):
            missing_documents.append(doc_type)
    
    if settings.DEBUG and missing_documents:
        print(f"Missing documents for application {getattr(application, 'reference_number', 'N/A')}: {missing_documents}")
    
    return len(missing_documents) == 0, missing_documents

# Add these catch-all functions to handle any other missing imports

def generate_reference_number():
    """
    Generate a unique reference number for applications.
    Format: CB-YYYY-XXXXX (e.g., CB-2025-00123)
    """
    import random
    from datetime import datetime
    
    year = datetime.now().year
    random_num = random.randint(10000, 99999)
    reference = f"CB-{year}-{random_num}"
    
    if settings.DEBUG:
        print(f"Generated reference number: {reference}")
    
    return reference


def check_application_deadline():
    """
    Check if the application deadline has passed.
    """
    from datetime import datetime
    
    # Example deadline - adjust based on your requirements
    deadline = datetime(2025, 12, 31, 23, 59, 59)
    now = datetime.now()
    
    is_open = now < deadline
    
    if settings.DEBUG:
        print(f"Application deadline check: {'Open' if is_open else 'Closed'}")
    
    return is_open


def export_applications_to_excel(applications):
    """
    Export applications to Excel format.
    """
    # Placeholder for Excel export functionality
    if settings.DEBUG:
        print(f"Exporting {len(applications)} applications to Excel")
    
    # You can implement actual Excel export using openpyxl or xlsxwriter
    return None


def bulk_approve_applications(application_ids, approved_by):
    """
    Bulk approve multiple applications.
    """
    if settings.DEBUG:
        print(f"Bulk approving {len(application_ids)} applications by {approved_by}")
    
    approved_count = 0
    # Implement actual bulk approval logic here
    
    return approved_count


def get_constituency_allocation():
    """
    Get the total allocation and remaining budget for the constituency.
    """
    allocation = {
        'total_budget': 5000000,  # Example: 5 million
        'allocated': 2000000,
        'remaining': 3000000,
        'percentage_used': 40,
    }
    
    if settings.DEBUG:
        print(f"Constituency allocation: {allocation}")
    
    return allocation

def export_applications_to_csv(applications, filename=None):
    """
    Export applications to CSV format.
    Returns CSV content as string or saves to file if filename provided.
    """
    import csv
    import io
    from datetime import datetime
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    headers = [
        'Reference Number',
        'Applicant Name',
        'Email',
        'Phone',
        'Institution',
        'Course',
        'Year of Study',
        'Amount Requested',
        'Family Income',
        'Status',
        'Score',
        'Date Submitted',
        'Academic Score',
        'Is Orphan',
        'Has Disability',
        'Ward',
        'Sub County'
    ]
    writer.writerow(headers)
    
    # Write application data
    for app in applications:
        row = [
            getattr(app, 'reference_number', ''),
            f"{getattr(app, 'first_name', '')} {getattr(app, 'last_name', '')}",
            getattr(app, 'email', ''),
            getattr(app, 'phone_number', ''),
            getattr(app, 'institution_name', ''),
            getattr(app, 'course_name', ''),
            getattr(app, 'year_of_study', ''),
            getattr(app, 'amount_requested', 0),
            getattr(app, 'family_income', 0),
            getattr(app, 'get_status_display', lambda: getattr(app, 'status', 'Unknown'))(),
            calculate_bursary_score(app),
            getattr(app, 'created_at', ''),
            getattr(app, 'academic_score', 0),
            'Yes' if getattr(app, 'is_orphan', False) else 'No',
            'Yes' if getattr(app, 'has_disability', False) else 'No',
            getattr(app, 'ward', ''),
            getattr(app, 'sub_county', '')
        ]
        writer.writerow(row)
    
    # Get CSV content
    csv_content = output.getvalue()
    output.close()
    
    # Save to file if filename provided
    if filename:
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                f.write(csv_content)
            if settings.DEBUG:
                print(f"Exported {len(applications)} applications to {filename}")
        except Exception as e:
            print(f"Error saving CSV file: {e}")
            return None
    
    return csv_content


def generate_application_report(start_date=None, end_date=None, status=None):
    """
    Generate a comprehensive report of applications.
    Can filter by date range and status.
    """
    from datetime import datetime, timedelta
    
    # Default date range if not provided
    if not end_date:
        end_date = datetime.now()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    report = {
        'report_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'period': {
            'start': start_date.strftime('%Y-%m-%d') if hasattr(start_date, 'strftime') else str(start_date),
            'end': end_date.strftime('%Y-%m-%d') if hasattr(end_date, 'strftime') else str(end_date),
        },
        'summary': {
            'total_applications': 0,
            'pending': 0,
            'approved': 0,
            'rejected': 0,
            'under_review': 0,
        },
        'financial_summary': {
            'total_requested': 0,
            'total_approved': 0,
            'total_disbursed': 0,
            'average_request': 0,
        },
        'demographic_summary': {
            'orphans': 0,
            'disabled': 0,
            'single_parent': 0,
            'male': 0,
            'female': 0,
        },
        'institution_summary': {},
        'ward_summary': {},
        'top_scorers': [],
        'recent_applications': [],
    }
    
    # In a real implementation, you would query your database here
    # For now, returning the empty report structure
    
    if settings.DEBUG:
        print(f"Generated report for period: {report['period']['start']} to {report['period']['end']}")
        if status:
            print(f"Filtered by status: {status}")
    
    return report


def format_currency(amount):
    """
    Format amount as currency (KES).
    """
    try:
        return f"KES {amount:,.2f}"
    except:
        return f"KES {amount}"


def get_application_timeline(application):
    """
    Get the timeline of status changes for an application.
    """
    # Placeholder - implement based on your status tracking
    timeline = [
        {
            'date': getattr(application, 'created_at', ''),
            'status': 'Submitted',
            'description': 'Application submitted',
        }
    ]
    
    if hasattr(application, 'reviewed_at') and application.reviewed_at:
        timeline.append({
            'date': application.reviewed_at,
            'status': 'Under Review',
            'description': 'Application under review',
        })
    
    if hasattr(application, 'approved_at') and application.approved_at:
        timeline.append({
            'date': application.approved_at,
            'status': 'Approved',
            'description': 'Application approved',
        })
    
    return timeline
