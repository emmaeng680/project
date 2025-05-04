from django import forms
from .models import Consultation, TPARequest

class ConsultationRequestForm(forms.ModelForm):
    """Form for requesting a neurologist consultation"""
    class Meta:
        model = Consultation
        fields = ['chief_complaint', 'notes']
        widgets = {
            'chief_complaint': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'})
        }
        help_texts = {
            'chief_complaint': 'Enter the primary reason for requesting neurologist consultation',
            'notes': 'Include any additional information that may be relevant for the neurologist'
        }

class ConsultationUpdateForm(forms.ModelForm):
    """Form for updating a consultation status and details"""
    class Meta:
        model = Consultation
        fields = ['status', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'})
        }

class ConsultationCompleteForm(forms.ModelForm):
    """Form for completing a consultation"""
    class Meta:
        model = Consultation
        fields = ['diagnosis', 'recommendations', 'notes']
        widgets = {
            'diagnosis': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'recommendations': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'})
        }
        help_texts = {
            'diagnosis': 'Enter your diagnosis based on patient assessment',
            'recommendations': 'Provide treatment recommendations and follow-up instructions',
            'notes': 'Additional notes or observations'
        }

class TPARequestForm(forms.ModelForm):
    """Form for requesting tPA administration"""
    class Meta:
        model = TPARequest
        fields = ['justification']
        widgets = {
            'justification': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'})
        }
        help_texts = {
            'justification': 'Detail why tPA administration is recommended for this patient'
        }
        labels = {
            'justification': 'Clinical justification for tPA'
        }

class TPAReviewForm(forms.ModelForm):
    """Form for reviewing tPA request by neurologist"""
    class Meta:
        model = TPARequest
        fields = ['status', 'review_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'review_notes': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'})
        }
        help_texts = {
            'status': 'Approve or deny the tPA administration request',
            'review_notes': 'Provide your clinical reasoning for this decision'
        }

class TPAAdministrationForm(forms.ModelForm):
    """Form for recording tPA administration details"""
    class Meta:
        model = TPARequest
        fields = ['administered', 'administration_notes']
        widgets = {
            'administered': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'administration_notes': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'})
        }
        help_texts = {
            'administered': 'Check this box to confirm tPA was administered',
            'administration_notes': 'Include time, dosage, patient response, and any complications'
        }