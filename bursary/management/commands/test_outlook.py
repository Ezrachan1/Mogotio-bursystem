# Save as test_outlook.py and run it
import smtplib
from email.mime.text import MIMEText

# Update these with your Outlook credentials
OUTLOOK_EMAIL = "your-email@outlook.com"  # Change this!
OUTLOOK_PASSWORD = "your-password"  # Your regular Outlook password

print(f"Testing Outlook SMTP for: {OUTLOOK_EMAIL}")

try:
    # Connect to Outlook SMTP
    server = smtplib.SMTP('smtp-mail.outlook.com', 587)
    server.starttls()
    server.login(OUTLOOK_EMAIL, OUTLOOK_PASSWORD)
    
    # Create message
    msg = MIMEText("This is a test email from Django Bursary System!")
    msg['Subject'] = 'Test Email from Django'
    msg['From'] = OUTLOOK_EMAIL
    msg['To'] = OUTLOOK_EMAIL
    
    # Send email
    server.send_message(msg)
    server.quit()
    
    print("✅ SUCCESS! Email sent successfully!")
    print("\nUse these settings in your Django settings.py:")
    print("-" * 50)
    print(f'EMAIL_HOST = "smtp-mail.outlook.com"')
    print(f'EMAIL_PORT = 587')
    print(f'EMAIL_USE_TLS = True')
    print(f'EMAIL_HOST_USER = "{OUTLOOK_EMAIL}"')
    print(f'EMAIL_HOST_PASSWORD = "{OUTLOOK_PASSWORD}"')
    print(f'DEFAULT_FROM_EMAIL = "{OUTLOOK_EMAIL}"')
    print("-" * 50)
    
except Exception as e:
    print(f"❌ Failed: {e}")
    print("\nTroubleshooting:")
    print("1. Enable POP/SMTP in Outlook settings (Mail → Sync email)")
    print("2. Check your password is correct")
    print("3. Make sure you're using your full email address")
    print("4. Try disabling 2FA temporarily if enabled")