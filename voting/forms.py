from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Voter

class VoterRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    voter_id = forms.CharField(max_length=20, required=True)
    phone = forms.CharField(max_length=15, required=True)
    address = forms.CharField(widget=forms.Textarea, required=True)
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=True
    )
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-input'})
        
        # Update password field help text
        self.fields['password1'].help_text = (
            'Password must be at least 8 characters and contain:<br>'
            '• At least one uppercase letter (A-Z)<br>'
            '• At least one lowercase letter (a-z)<br>'
            '• At least one number (0-9)'
        )
    
    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        
        # Custom validation for password strength
        if len(password) < 8:
            raise forms.ValidationError('Password must be at least 8 characters long.')
        
        if not any(char.isupper() for char in password):
            raise forms.ValidationError('Password must contain at least one uppercase letter.')
        
        if not any(char.islower() for char in password):
            raise forms.ValidationError('Password must contain at least one lowercase letter.')
        
        if not any(char.isdigit() for char in password):
            raise forms.ValidationError('Password must contain at least one number.')
        
        return password
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.is_active = False  # User must verify email before logging in
        
        if commit:
            user.save()
            Voter.objects.create(
                user=user,
                voter_id=self.cleaned_data['voter_id'],
                phone=self.cleaned_data['phone'],
                address=self.cleaned_data['address'],
                date_of_birth=self.cleaned_data['date_of_birth'],
                email_verified=False  # New field
            )
        return user

class LoginForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-input'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input'}))
