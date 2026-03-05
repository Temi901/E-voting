def send_verification_email(user, request):
    """Send email verification link to user"""
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.http import urlsafe_base64_encode
    from django.utils.encoding import force_bytes
    from django.core.mail import send_mail
    from django.conf import settings
    from django.utils.html import strip_tags
    
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    verification_url = f"{settings.SITE_URL}/verify-email/{uid}/{token}/"
    
    subject = 'Verify Your E-Voting Account'
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #1a3c5e;">Welcome to E-Voting System!</h2>
            <p>Hello {user.first_name},</p>
            <p>Thank you for registering. Please verify your email address by clicking the button below:</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{verification_url}" 
                   style="background-color: #1a3c5e; color: white; padding: 12px 30px; 
                          text-decoration: none; border-radius: 5px; display: inline-block;">
                    Verify Email Address
                </a>
            </div>
            <p>Or copy and paste this link into your browser:</p>
            <p style="background-color: #f5f5f5; padding: 10px; word-break: break-all;">
                {verification_url}
            </p>
            <p style="color: #666; font-size: 14px;">
                This link will expire in 24 hours. If you didn't create an account, please ignore this email.
            </p>
        </div>
    </body>
    </html>
    """
    
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_password_reset_email(user, request):
    """Send password reset link to user"""
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.http import urlsafe_base64_encode
    from django.utils.encoding import force_bytes
    from django.core.mail import send_mail
    from django.conf import settings
    from django.utils.html import strip_tags
    
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    reset_url = f"{settings.SITE_URL}/reset-password/{uid}/{token}/"
    
    subject = 'Reset Your E-Voting Password'
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #1a3c5e;">Password Reset Request</h2>
            <p>Hello {user.first_name},</p>
            <p>We received a request to reset your password. Click the button below to create a new password:</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}" 
                   style="background-color: #1a3c5e; color: white; padding: 12px 30px; 
                          text-decoration: none; border-radius: 5px; display: inline-block;">
                    Reset Password
                </a>
            </div>
            <p>Or copy and paste this link into your browser:</p>
            <p style="background-color: #f5f5f5; padding: 10px; word-break: break-all;">
                {reset_url}
            </p>
            <p style="color: #666; font-size: 14px;">
                This link will expire in 24 hours. If you didn't request a password reset, please ignore this email.
            </p>
        </div>
    </body>
    </html>
    """
    
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_vote_confirmation_email(user, election, candidate):
    """Send vote confirmation email to voter"""
    from django.core.mail import send_mail
    from django.conf import settings
    from django.utils.html import strip_tags
    
    subject = f'Vote Confirmation - {election.title}'
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #1a3c5e;">Vote Confirmed! ✓</h2>
            <p>Hello {user.first_name},</p>
            <p>Your vote has been successfully recorded for:</p>
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 5px 0;"><strong>Election:</strong> {election.title}</p>
                <p style="margin: 5px 0;"><strong>Your Vote:</strong> {candidate.name}</p>
            </div>
            <p style="color: #666; font-size: 14px;">
                Thank you for participating in this election. Your vote has been encrypted and securely stored.
            </p>
        </div>
    </body>
    </html>
    """
    
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=False,
    )

def send_results_available_email(election):
    """
    Send email to all voters when election results become available
    """
    # Check if we've already sent this email
    if EmailLog.objects.filter(election=election, email_type='results_available').exists():
        print(f"Already sent 'results_available' email for {election.title}")
        return 0
    
    # Get all voters who voted in this election
    votes = Vote.objects.filter(election=election).select_related('voter__user')
    
    if not votes.exists():
        return 0  # No votes to send emails to
    
    emails_sent = 0
    
    for vote in votes:
        user = vote.voter.user
        
        if not user.email:
            continue  # Skip users without email
        
        # Prepare email content
        subject = f'🎉 Results Available: {election.title}'
        
        message = f"""
Hello {user.first_name},

Great news! The election "{election.title}" has ended and results are now available!

📊 VIEW RESULTS NOW:
{settings.SITE_URL}/results/{election.id}/

⏰ IMPORTANT: Results will be available for 24 hours only!
Results expire on: {election.get_results_expiry_time().strftime('%B %d, %Y at %I:%M %p')}

Thank you for participating in this election!

---
E-Voting System
Secure • Transparent • Democratic
        """
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@evoting.com',
                recipient_list=[user.email],
                fail_silently=False,
            )
            emails_sent += 1
            print(f"✓ Sent to {user.email}")
        except Exception as e:
            print(f"✗ Failed to send email to {user.email}: {e}")
    
    # Log that we sent this email
    EmailLog.objects.create(
        election=election,
        email_type='results_available',
        recipient_count=emails_sent
    )
    
    return emails_sent


def send_results_expiring_soon_email(election):
    """
    Send reminder email 1 hour before results expire (23 hours after election ends)
    """
    # Check if we've already sent this email
    if EmailLog.objects.filter(election=election, email_type='results_expiring').exists():
        print(f"Already sent 'results_expiring' email for {election.title}")
        return 0
    
    votes = Vote.objects.filter(election=election).select_related('voter__user')
    
    if not votes.exists():
        return 0
    
    emails_sent = 0
    
    for vote in votes:
        user = vote.voter.user
        
        if not user.email:
            continue
        
        subject = f'⏰ Last Chance: Results Expiring Soon - {election.title}'
        
        message = f"""
Hello {user.first_name},

⚠️ REMINDER: Results for "{election.title}" will expire in approximately 1 HOUR!

This is your last chance to view the final election results.

📊 VIEW RESULTS NOW:
{settings.SITE_URL}/results/{election.id}/

⏰ Results expire on: {election.get_results_expiry_time().strftime('%B %d, %Y at %I:%M %p')}

Don't miss your opportunity to see the final results!

---
E-Voting System
Secure • Transparent • Democratic
        """
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@evoting.com',
                recipient_list=[user.email],
                fail_silently=False,
            )
            emails_sent += 1
            print(f"✓ Sent to {user.email}")
        except Exception as e:
            print(f"✗ Failed to send email to {user.email}: {e}")
    
    # Log that we sent this email
    EmailLog.objects.create(
        election=election,
        email_type='results_expiring',
        recipient_count=emails_sent
    )
    
    return emails_sent


def send_test_email(user_email):
    """
    Send a test email to verify email configuration
    """
    subject = 'Test Email from E-Voting System'
    message = """
Hello!

This is a test email from your E-Voting System.

If you're receiving this, your email configuration is working correctly! ✓

---
E-Voting System
    """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@evoting.com',
            recipient_list=[user_email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send test email: {e}")
        return False

def send_password_reset_email(user, request):
    """Send password reset link to user"""
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.http import urlsafe_base64_encode
    from django.utils.encoding import force_bytes
    from django.core.mail import send_mail
    from django.conf import settings
    from django.utils.html import strip_tags
    
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    reset_url = f"{settings.SITE_URL}/reset-password/{uid}/{token}/"
    
    subject = 'Reset Your E-Voting Password'
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #1a3c5e;">Password Reset Request</h2>
            <p>Hello {user.first_name},</p>
            <p>We received a request to reset your password. Click the button below to create a new password:</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}" 
                   style="background-color: #1a3c5e; color: white; padding: 12px 30px; 
                          text-decoration: none; border-radius: 5px; display: inline-block;">
                    Reset Password
                </a>
            </div>
            <p>Or copy and paste this link into your browser:</p>
            <p style="background-color: #f5f5f5; padding: 10px; word-break: break-all;">
                {reset_url}
            </p>
            <p style="color: #666; font-size: 14px;">
                This link will expire in 24 hours. If you didn't request a password reset, please ignore this email.
            </p>
        </div>
    </body>
    </html>
    """
    
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_vote_confirmation_email(user, election, candidate):
    """Send vote confirmation email to voter"""
    from django.core.mail import send_mail
    from django.conf import settings
    from django.utils.html import strip_tags
    
    subject = f'Vote Confirmation - {election.title}'
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #1a3c5e;">Vote Confirmed! ✓</h2>
            <p>Hello {user.first_name},</p>
            <p>Your vote has been successfully recorded for:</p>
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 5px 0;"><strong>Election:</strong> {election.title}</p>
                <p style="margin: 5px 0;"><strong>Your Vote:</strong> {candidate.name}</p>
            </div>
            <p style="color: #666; font-size: 14px;">
                Thank you for participating in this election. Your vote has been encrypted and securely stored.
            </p>
        </div>
    </body>
    </html>
    """
    
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=False,
    )
