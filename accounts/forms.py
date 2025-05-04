from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, TechnicianProfile, NeurologistProfile, PatientProfile

class UserRegistrationForm(UserCreationForm):
    """Form for user registration with role selection"""
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'role', 'password1', 'password2']
        widgets = {
            'role': forms.RadioSelect()
        }

class TechnicianProfileForm(forms.ModelForm):
    """Form for technician-specific profile information"""
    class Meta:
        model = TechnicianProfile
        fields = ['license_number', 'certification', 'unit_number']

class NeurologistProfileForm(forms.ModelForm):
    """Form for neurologist-specific profile information"""
    class Meta:
        model = NeurologistProfile
        fields = ['medical_license', 'specialty', 'years_of_experience']

class PatientProfileForm(forms.ModelForm):
    """Form for patient-specific profile information"""
    class Meta:
        model = PatientProfile
        fields = ['date_of_birth', 'medical_history', 'current_medications']

class UserProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile information"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number']