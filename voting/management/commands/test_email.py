from django.core.management.base import BaseCommand
from voting.email_utils import send_test_email

class Command(BaseCommand):
    help = 'Send a test email to verify email configuration'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email address to send test to')

    def handle(self, *args, **options):
        email = options['email']
        
        self.stdout.write(f'Sending test email to: {email}')
        
        success = send_test_email(email)
        
        if success:
            self.stdout.write(self.style.SUCCESS(f'✓ Test email sent successfully!'))
            self.stdout.write('Check your console/terminal for the email content.')
        else:
            self.stdout.write(self.style.ERROR('✗ Failed to send test email'))