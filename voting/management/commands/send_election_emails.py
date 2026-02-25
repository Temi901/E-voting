from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from voting.models import Election
from voting.email_utils import send_results_available_email, send_results_expiring_soon_email

class Command(BaseCommand):
    help = 'Send email notifications for election results'

    def handle(self, *args, **options):
        now = timezone.now()
        
        # Check for elections that just ended (within last 5 minutes)
        # Send "results available" emails
        recently_ended = Election.objects.filter(
            is_active=True,
            end_date__lte=now,
            end_date__gte=now - timedelta(minutes=5)
        )
        
        for election in recently_ended:
            self.stdout.write(f'Sending results available emails for: {election.title}')
            emails_sent = send_results_available_email(election)
            self.stdout.write(self.style.SUCCESS(f'  ✓ Sent {emails_sent} emails'))
        
        # Check for elections where results will expire in ~1 hour (23 hours after end)
        # Send "results expiring soon" reminder emails
        expiring_soon = Election.objects.filter(
            is_active=True,
            end_date__lte=now - timedelta(hours=23),
            end_date__gte=now - timedelta(hours=23, minutes=5)
        )
        
        for election in expiring_soon:
            self.stdout.write(f'Sending expiring soon emails for: {election.title}')
            emails_sent = send_results_expiring_soon_email(election)
            self.stdout.write(self.style.SUCCESS(f'  ✓ Sent {emails_sent} emails'))
        
        if not recently_ended and not expiring_soon:
            self.stdout.write(self.style.WARNING('No emails to send at this time.'))