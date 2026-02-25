from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import Vote, Election, EmailLog

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