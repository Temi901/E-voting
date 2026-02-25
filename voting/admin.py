from django.contrib import admin
from .models import Voter, Election, Candidate, Vote, EmailLog

@admin.register(Voter)
class VoterAdmin(admin.ModelAdmin):
    list_display = ['user', 'voter_id', 'phone', 'has_voted', 'created_at']
    list_filter = ['has_voted', 'created_at']
    search_fields = ['user__username', 'voter_id', 'phone']
    readonly_fields = ['created_at']

@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'start_date', 'end_date', 'is_active', 'created_at']
    list_filter = ['is_active', 'start_date', 'end_date']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at']

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ['name', 'party', 'election', 'created_at']
    list_filter = ['election', 'party', 'created_at']
    search_fields = ['name', 'party']
    readonly_fields = ['created_at']

@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ['voter', 'election', 'candidate', 'timestamp']
    list_filter = ['election', 'timestamp']
    search_fields = ['voter__user__username', 'candidate__name']
    readonly_fields = ['timestamp']
    
    def has_add_permission(self, request):
        # Prevent manual vote creation through admin
        return False
    
    def has_change_permission(self, request, obj=None):
        # Prevent vote modification   
        return False
@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ['election', 'email_type', 'recipient_count', 'sent_at']
    list_filter = ['email_type', 'sent_at']
    search_fields = ['election__title']
    readonly_fields = ['election', 'email_type', 'sent_at', 'recipient_count']
    
    def has_add_permission(self, request):
        # Prevent manual creation
        return False
    
    def has_change_permission(self, request, obj=None):
        # View only
        return False
        