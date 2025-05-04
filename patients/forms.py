from django import forms
from django.contrib.auth import get_user_model
from accounts.models import User
from .models import Patient

class PatientRegistrationForm(forms.ModelForm):
    """Form for registering a new patient"""
    # Add more detailed fields for the medical history
    hypertension = forms.BooleanField(required=False)
    diabetes = forms.BooleanField(required=False)
    hyperlipidemia = forms.BooleanField(required=False)
    coronary_artery_disease = forms.BooleanField(required=False)
    atrial_fibrillation = forms.BooleanField(required=False)
    prior_stroke = forms.BooleanField(required=False)
    smoking = forms.BooleanField(required=False)
    alcohol_use = forms.BooleanField(required=False)
    
    # Emergency contact relationship field (not in model, but we'll handle it)
    emergency_contact_relationship = forms.CharField(max_length=100, required=False)
    
    # Email for patient account
    email = forms.EmailField(required=False)
    
    # Optional MRN field if it exists in the model
    if hasattr(Patient, 'mrn'):
        mrn = forms.CharField(max_length=20, required=False, label="Medical Record Number (MRN)")
    
    class Meta:
        model = Patient
        fields = [
            'first_name', 'last_name', 'date_of_birth', 'gender', 
            'phone_number', 'address', 'emergency_contact_name',
            'emergency_contact_phone', 'medical_history', 
            'current_medications', 'allergies',
        ]
        
        # Add mrn to fields if it exists in the model
        if hasattr(Patient, 'mrn'):
            fields.append('mrn')
            
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'medical_history': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter any additional medical history details here'}),
            'current_medications': forms.Textarea(attrs={'rows': 4, 'placeholder': 'List all current medications and dosages'}),
            'allergies': forms.Textarea(attrs={'rows': 4, 'placeholder': 'List any known allergies (medications, food, etc.)'}),
            'address': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Full address including street, city, state and zip code'}),
        }
    
    def save(self, commit=True):
        # Get the cleaned data
        data = self.cleaned_data
        
        # Create or update patient record
        patient = super().save(commit=False)
        
        # Extract medical conditions for structured storage
        medical_conditions = []
        if data.get('hypertension'):
            medical_conditions.append('Hypertension')
        if data.get('diabetes'):
            medical_conditions.append('Diabetes')
        if data.get('hyperlipidemia'):
            medical_conditions.append('Hyperlipidemia')
        if data.get('coronary_artery_disease'):
            medical_conditions.append('Coronary Artery Disease')
        if data.get('atrial_fibrillation'):
            medical_conditions.append('Atrial Fibrillation')
        if data.get('prior_stroke'):
            medical_conditions.append('Prior Stroke')
        if data.get('smoking'):
            medical_conditions.append('Smoking')
        if data.get('alcohol_use'):
            medical_conditions.append('Alcohol Use')
        
        # Add these to the medical history text field
        if medical_conditions:
            condition_list = ", ".join(medical_conditions)
            if patient.medical_history:
                patient.medical_history += f"\n\nMedical Conditions: {condition_list}"
            else:
                patient.medical_history = f"Medical Conditions: {condition_list}"
        
        # Add emergency contact relationship to the emergency contact name if provided
        if data.get('emergency_contact_relationship') and data.get('emergency_contact_name'):
            patient.emergency_contact_name += f" ({data['emergency_contact_relationship']})"
        
        # Generate access code if the field exists
        if hasattr(patient, 'access_code') and not patient.access_code and hasattr(patient, 'generate_access_code'):
            patient.access_code = patient.generate_access_code()
        
        # Save chief complaint and onset time if they're in the form
        if 'chief_complaint' in data and data.get('chief_complaint'):
            if hasattr(patient, 'chief_complaint'):
                patient.chief_complaint = data.get('chief_complaint')
        
        if 'onset_time' in data and data.get('onset_time'):
            if hasattr(patient, 'onset_time'):
                patient.onset_time = data.get('onset_time')
        
        # Save vital signs if they're in the form
        has_vitals = any([
            data.get('blood_pressure_systolic'),
            data.get('blood_pressure_diastolic'),
            data.get('heart_rate'),
            data.get('respiratory_rate'),
            data.get('temperature'),
            data.get('oxygen_saturation'),
            data.get('blood_glucose')
        ])
        
        if commit:
            patient.save()
            
            # If we have vitals data, create a VitalSigns record if the model exists
            if has_vitals:
                try:
                    from django.apps import apps
                    try:
                        VitalSigns = apps.get_model('assessments', 'VitalSigns')
                    except:
                        VitalSigns = apps.get_model('patients', 'VitalSigns')
                    
                    vitals = VitalSigns(
                        patient=patient,
                        systolic=data.get('blood_pressure_systolic'),
                        diastolic=data.get('blood_pressure_diastolic'),
                        heart_rate=data.get('heart_rate'),
                        respiratory_rate=data.get('respiratory_rate'),
                        temperature=data.get('temperature'),
                        oxygen_saturation=data.get('oxygen_saturation'),
                        blood_glucose=data.get('blood_glucose'),
                        recorded_by=patient.registered_by if hasattr(patient, 'registered_by') else None
                    )
                    vitals.save()
                except Exception as e:
                    print(f"Error creating vital signs record: {e}")
            
            # Create a user account for the patient if email is provided
            if data.get('email'):
                try:
                    # Check if user already exists
                    User = get_user_model()
                    user, created = User.objects.get_or_create(
                        username=data['email'],
                        defaults={
                            'email': data['email'],
                            'first_name': data['first_name'],
                            'last_name': data['last_name'],
                            'role': 'PATIENT' if hasattr(User, 'role') else None
                        }
                    )
                    
                    # If user was created, set a random password
                    if created:
                        user.set_password(User.objects.make_random_password())
                        if hasattr(user, 'is_patient'):
                            user.is_patient = True
                        user.save()
                        
                        # Link patient to user if not already linked
                        patient.user_account = user
                        patient.save()
                except Exception as e:
                    print(f"Error creating user account: {e}")
        
        return patient


class PatientForm(forms.ModelForm):
    """Form for editing an existing patient"""
    class Meta:
        model = Patient
        fields = ['first_name', 'last_name', 'date_of_birth', 'gender', 'phone_number', 
                 'address', 'emergency_contact_name', 'emergency_contact_phone',
                 'medical_history', 'current_medications', 'allergies']
        
        # Add optional fields if they exist
        if hasattr(Patient, 'mrn'):
            fields.append('mrn')
        if hasattr(Patient, 'email'):
            fields.append('email')
        if hasattr(Patient, 'access_code'):
            fields.append('access_code')
            
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'medical_history': forms.Textarea(attrs={'rows': 4}),
            'current_medications': forms.Textarea(attrs={'rows': 4}),
            'allergies': forms.Textarea(attrs={'rows': 4}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }


class ResetAccessCodeForm(forms.Form):
    """Form for confirming access code reset"""
    confirm = forms.BooleanField(
        label="I confirm that I want to generate a new access code for this patient",
        required=True
    )