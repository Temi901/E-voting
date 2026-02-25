from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.utils import timezone
from .models import Voter, Election, Candidate, Vote
from .forms import VoterRegistrationForm, LoginForm
from django.http import HttpResponse
from .export_utils import generate_results_pdf, generate_results_excel
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count


def index(request):
    """Homepage view"""
    elections = Election.objects.filter(is_active=True).order_by('-start_date')[:3]
    return render(request, 'voting/index.html', {'elections': elections})

def register_view(request):
    """Voter registration view"""
    if request.method == 'POST':
        form = VoterRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to E-Voting.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Registration failed. Please correct the errors.')
    else:
        form = VoterRegistrationForm()
    
    return render(request, 'voting/register.html', {'form': form})

def login_view(request):
    """User login view"""
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    
    return render(request, 'voting/login.html', {'form': form})

@login_required
def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('index')

@login_required
def dashboard(request):
    """User dashboard view"""
    from django.utils import timezone
    from datetime import timedelta
    
    try:
        voter = request.user.voter
    except Voter.DoesNotExist:
        messages.error(request, 'Voter profile not found.')
        return redirect('index')
    
    # Get ALL active elections (not just ongoing ones)
    all_elections = Election.objects.filter(is_active=True).order_by('-created_at')
    
    # Filter to show: ongoing elections OR elections that ended within last 24 hours
    now = timezone.now()
    elections_to_show = []
    
    for election in all_elections:
        # Show if election is ongoing
        if election.is_ongoing():
            elections_to_show.append(election)
        # OR show if election ended but still within 24-hour results window
        elif election.has_ended() and election.results_available_for_24hr():
            elections_to_show.append(election)
    
    voted_elections = Vote.objects.filter(voter=voter).values_list('election_id', flat=True)
    
    # Get vote details for each election (for 24hr timer)
    user_votes = Vote.objects.filter(voter=voter).select_related('election')
    vote_details = {}
    for vote in user_votes:
        time_since_vote = timezone.now() - vote.timestamp
        time_remaining = timedelta(hours=24) - time_since_vote
        
        if time_remaining.total_seconds() > 0:
            hours = int(time_remaining.total_seconds() // 3600)
            minutes = int((time_remaining.total_seconds() % 3600) // 60)
            vote_details[vote.election_id] = {
                'can_view': True,
                'hours': hours,
                'minutes': minutes,
            }
        else:
            vote_details[vote.election_id] = {
                'can_view': False,
            }
    
    context = {
        'voter': voter,
        'elections': elections_to_show,
        'voted_elections': voted_elections,
        'vote_details': vote_details,
    }
    return render(request, 'voting/dashboard.html', context)

@login_required
def vote_view(request, election_id):
    """Voting view"""
    election = get_object_or_404(Election, id=election_id)
    voter = request.user.voter
    
    # Check if election is ongoing
    if not election.is_ongoing():
        messages.error(request, 'This election is not currently active.')
        return redirect('dashboard')
    
    # Check if user has already voted
    if Vote.objects.filter(voter=voter, election=election).exists():
        messages.warning(request, 'You have already voted in this election.')
        return redirect('results', election_id=election_id)
    
    candidates = election.candidates.all()
    
    if request.method == 'POST':
        candidate_id = request.POST.get('candidate_id')
        candidate = get_object_or_404(Candidate, id=candidate_id, election=election)
        
        # Create vote
        Vote.objects.create(
            voter=voter,
            election=election,
            candidate=candidate
        )
        
        # Mark voter as having voted
        voter.has_voted = True
        voter.save()
        
        messages.success(request, f'Your vote for {candidate.name} has been recorded successfully!')
        return redirect("dashboard")
    
    context = {
        'election': election,
        'candidates': candidates,
    }
    return render(request, 'voting/vote.html', context)

@login_required
def results_view(request, election_id):
    """Election results view - Available for 24 hours after election ends"""
    from datetime import timedelta
    from django.utils import timezone
    
    election = get_object_or_404(Election, id=election_id)
    
    # Check if user has voted
    try:
        user_vote = Vote.objects.get(
            voter=request.user.voter,
            election=election
        )
        user_voted = True
    except Vote.DoesNotExist:
        user_voted = False
    
    # Calculate time remaining in 24-hour window (after election ends)
    hours_remaining = 0
    minutes_remaining = 0
    
    if election.has_ended():
        time_since_end = timezone.now() - election.end_date
        time_remaining = timedelta(hours=24) - time_since_end
        
        if time_remaining.total_seconds() > 0:
            hours_remaining = int(time_remaining.total_seconds() // 3600)
            minutes_remaining = int((time_remaining.total_seconds() % 3600) // 60)
    
    # ===== ACCESS CONTROL LOGIC =====
    
    # CASE 1: Election is still ongoing - BLOCK everyone
    if election.is_ongoing():
        if user_voted:
            messages.info(request, f'Results will be available for 24 hours after the election ends on {election.end_date.strftime("%B %d, %Y at %I:%M %p")}.')
        else:
            messages.warning(request, 'Please cast your vote. Results will be available after the election ends.')
        return redirect('dashboard')
    
    # CASE 2: Election ended and within 24-hour window - ALLOW everyone who voted
    elif election.has_ended() and election.results_available_for_24hr():
        if not user_voted:
            messages.warning(request, 'You must have voted in this election to view results.')
            return redirect('dashboard')
        access_reason = "24hr_window"
    
    # CASE 3: Election ended and 24-hour window expired - BLOCK everyone
    elif election.has_ended() and not election.results_available_for_24hr():
        expiry_time = election.get_results_expiry_time()
        messages.info(request, f'The 24-hour results viewing period expired on {expiry_time.strftime("%B %d, %Y at %I:%M %p")}.')
        return redirect('dashboard')
    
    # CASE 4: Any other situation - BLOCK
    else:
        messages.info(request, 'Results are not currently available.')
        return redirect('dashboard')
    
    # Get candidates with vote counts
    candidates = election.candidates.annotate(
        vote_count=Count('votes')
    ).order_by('-vote_count')
    
    total_votes = Vote.objects.filter(election=election).count()
    
    # Calculate percentage for each candidate
    candidates_with_percentage = []
    for candidate in candidates:
        percentage = round((candidate.vote_count / total_votes * 100), 2) if total_votes > 0 else 0
        candidates_with_percentage.append({
            'id': candidate.id,
            'name': candidate.name,
            'party': candidate.party,
            'photo': candidate.photo,
            'biography': candidate.biography,
            'vote_count': candidate.vote_count,
            'percentage': percentage,
        })
    
    context = {
        'election': election,
        'candidates': candidates_with_percentage,
        'total_votes': total_votes,
        'user_voted': user_voted,
        'access_reason': access_reason,
        'hours_remaining': hours_remaining,
        'minutes_remaining': minutes_remaining,
    }
    return render(request, 'voting/results.html', context)
@login_required
def export_results_pdf(request, election_id):
    """
    Export election results as PDF
    """
    election = get_object_or_404(Election, id=election_id)
    voter = get_object_or_404(Voter, user=request.user)
    
    # Check if voter participated in this election
    vote = Vote.objects.filter(voter=voter, election=election).first()
    
    if not vote:
        messages.error(request, "You can only download results for elections you participated in.")
        return redirect('dashboard')
    
    # Check if election has ended
    if not election.has_ended():
        messages.error(request, "Results are not available yet. Election is still ongoing.")
        return redirect('dashboard')
    
    # Check if results are still within 24-hour window
    if not election.results_available_for_24hr():
        messages.error(request, "Results are no longer available. The 24-hour viewing window has expired.")
        return redirect('dashboard')
    
    # Generate PDF
    pdf_buffer = generate_results_pdf(election)
    
    # Create response
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    filename = f"{election.title.replace(' ', '_')}_Results.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


@login_required
def export_results_excel(request, election_id):
    """
    Export election results as Excel
    """
    election = get_object_or_404(Election, id=election_id)
    voter = get_object_or_404(Voter, user=request.user)
    
    # Check if voter participated in this election
    vote = Vote.objects.filter(voter=voter, election=election).first()
    
    if not vote:
        messages.error(request, "You can only download results for elections you participated in.")
        return redirect('dashboard')
    
    # Check if election has ended
    if not election.has_ended():
        messages.error(request, "Results are not available yet. Election is still ongoing.")
        return redirect('dashboard')
    
    # Check if results are still within 24-hour window
    if not election.results_available_for_24hr():
        messages.error(request, "Results are no longer available. The 24-hour viewing window has expired.")
        return redirect('dashboard')
    
    # Generate Excel
    excel_buffer = generate_results_excel(election)
    
    # Create response
    response = HttpResponse(
        excel_buffer,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"{election.title.replace(' ', '_')}_Results.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

@staff_member_required
def admin_dashboard(request):
    """
    Admin dashboard to monitor all elections
    """
    # Get all elections
    elections = Election.objects.all().order_by('-created_at')
    
    # Statistics
    total_elections = elections.count()
    active_elections = elections.filter(is_active=True, end_date__gt=timezone.now()).count()
    completed_elections = elections.filter(end_date__lt=timezone.now()).count()
    total_voters = Voter.objects.count()
    total_votes = Vote.objects.count()
    
    # Recent activity
    recent_votes = Vote.objects.select_related('voter__user', 'election', 'candidate').order_by('-timestamp')[:10]
    
    # Election data for charts
    election_data = []
    for election in elections[:5]:  # Last 5 elections
        candidates = election.candidates.all()
        candidate_names = [c.name for c in candidates]
        vote_counts = [c.vote_count() for c in candidates]
        
        election_data.append({
            'election': election,
            'candidate_names': candidate_names,
            'vote_counts': vote_counts,
            'total_votes': sum(vote_counts),
        })
    
    context = {
        'total_elections': total_elections,
        'active_elections': active_elections,
        'completed_elections': completed_elections,
        'total_voters': total_voters,
        'total_votes': total_votes,
        'elections': elections,
        'recent_votes': recent_votes,
        'election_data': election_data,
    }
    
    return render(request, 'voting/admin_dashboard.html', context)