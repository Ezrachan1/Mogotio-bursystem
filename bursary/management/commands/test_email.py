from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Test email configuration by sending a test email'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--to',
            type=str,
            default=None,
            help='Email address to send test email to',
        )
    
    def handle(self, *args, **options):
        to_email = options.get('to') or settings.DEFAULT_FROM_EMAIL
        
        if not to_email:
            self.stdout.write(
                self.style.ERROR('No email address provided. Use --to parameter or set DEFAULT_FROM_EMAIL in settings.')
            )
            return
        
        self.stdout.write('Testing email configuration...')
        self.stdout.write(f'SMTP Server: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}')
        self.stdout.write(f'From: {settings.DEFAULT_FROM_EMAIL}')
        self.stdout.write(f'To: {to_email}')
        self.stdout.write(f'TLS: {settings.EMAIL_USE_TLS}')
        
        try:
            send_mail(
                subject='Test Email from Bursary System',
                message='''This is a test email from your Constituency Bursary System.

If you received this email, your email configuration is working correctly!

Configuration details:
- SMTP Host: {}
- SMTP Port: {}
- From Email: {}

Best regards,
Bursary System
'''.format(settings.EMAIL_HOST, settings.EMAIL_PORT, settings.DEFAULT_FROM_EMAIL),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                fail_silently=False,
            )
            self.stdout.write(
                self.style.SUCCESS(f'✓ Email sent successfully to {to_email}! Check your inbox.')
            )
            
            # Additional tips
            self.stdout.write('\nTips:')
            self.stdout.write('- Check your spam folder if you don\'t see the email')
            self.stdout.write('- Make sure you\'re using an App Password, not your regular Gmail password')
            self.stdout.write('- Ensure 2-Factor Authentication is enabled on your Gmail account')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Failed to send email: {str(e)}')
            )
            
            # Provide helpful debugging information
            self.stdout.write('\nTroubleshooting tips:')
            
            if 'authentication' in str(e).lower():
                self.stdout.write('- Make sure you\'re using an App Password from Gmail')
                self.stdout.write('- Check that 2FA is enabled on your Google account')
                self.stdout.write('- Verify EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in settings')
            
            if 'connection' in str(e).lower():
                self.stdout.write('- Check your internet connection')
                self.stdout.write('- Verify EMAIL_HOST and EMAIL_PORT settings')
                self.stdout.write('- Try EMAIL_PORT=587 with EMAIL_USE_TLS=True')
            
            if not hasattr(settings, 'EMAIL_HOST_PASSWORD') or not settings.EMAIL_HOST_PASSWORD:
                self.stdout.write(
                    self.style.WARNING('- EMAIL_HOST_PASSWORD is not set in settings!')
                )
