from django.db import models
from accounts.models import User
from django.utils.crypto import get_random_string

class Patient(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    # Existing fields - unchanged
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True)
    medical_history = models.TextField(blank=True)
    current_medications = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    registered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='registered_patients')
    registration_date = models.DateTimeField(auto_now_add=True)
    user_account = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='patient_record')
    
    # New fields for patient portal access
    access_code = models.CharField(max_length=8, unique=True, blank=True, null=True)
    access_code_expiry = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    # New methods for managing access codes
    def generate_access_code(self):
        """Generate a unique 8-character access code"""
        code = get_random_string(8).upper()
        # Make sure it's unique
        while Patient.objects.filter(access_code=code).exists():
            code = get_random_string(8).upper()
        return code
    
    def reset_access_code(self):
        """Generate a new access code for the patient"""
        self.access_code = self.generate_access_code()
        self.save()
        return self.access_code
    
    class Meta:
        ordering = ['-registration_date']