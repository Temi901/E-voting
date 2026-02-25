from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Voter(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    voter_id = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    date_of_birth = models.DateField()
    has_voted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.voter_id}"

class Election(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def is_ongoing(self):
        now = timezone.now()
        return self.start_date <= now <= self.end_date and self.is_active

    def has_ended(self):
        """Check if election has ended or is inactive"""
        now = timezone.now()
        return now > self.end_date or not self.is_active
    
    def results_available_for_24hr(self):
        """Check if results are available (election ended and within 24 hours)"""
        from django.utils import timezone
        from datetime import timedelta
        
        if not self.has_ended():
            return False
        
        now = timezone.now()
        time_since_end = now - self.end_date
        return time_since_end <= timedelta(hours=24)

    def get_results_expiry_time(self):
        """Get when the 24-hour results window expires"""
        from datetime import timedelta
        return self.end_date + timedelta(hours=24)

class Candidate(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='candidates')
    name = models.CharField(max_length=100)
    party = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='candidates/', blank=True, null=True)
    biography = models.TextField()
    manifesto = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.party}"

    def vote_count(self):
        return self.votes.count()

class Vote(models.Model):
    voter = models.ForeignKey(Voter, on_delete=models.CASCADE)
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='votes')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('voter', 'election')

    def __str__(self):
        return f"Vote by {self.voter.user.username} in {self.election.title}"
    
    def can_view_results(self):
        """Check if voter can view results (within 24 hours of voting)"""
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        time_since_vote = now - self.timestamp
        return time_since_vote <= timedelta(hours=24)


class EmailLog(models.Model):
    """Track sent emails to prevent duplicates"""
    EMAIL_TYPES = (
        ('results_available', 'Results Available'),
        ('results_expiring', 'Results Expiring Soon'),
    )
    
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    email_type = models.CharField(max_length=20, choices=EMAIL_TYPES)
    sent_at = models.DateTimeField(auto_now_add=True)
    recipient_count = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ('election', 'email_type')
    
    def __str__(self):
        return f"{self.email_type} - {self.election.title}"