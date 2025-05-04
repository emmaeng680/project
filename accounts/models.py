from django.db import models
from django.contrib.auth.models import AbstractUser



class User(AbstractUser):
    class Role(models.TextChoices):
        PATIENT = 'PATIENT', 'Patient'
        TECHNICIAN = 'TECHNICIAN', 'Technician'
        NEUROLOGIST = 'NEUROLOGIST', 'Neurologist'
    
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.PATIENT
    )
    phone_number = models.CharField(max_length=15, blank=True)
    
    # Add related_name to avoid clash with auth.User model
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )
    
    @property
    def is_patient(self):
        return self.role == self.Role.PATIENT
    
    @property
    def is_technician(self):
        return self.role == self.Role.TECHNICIAN
    
    @property
    def is_neurologist(self):
        return self.role == self.Role.NEUROLOGIST

class TechnicianProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='technician_profile')
    license_number = models.CharField(max_length=50, blank=True)
    certification = models.CharField(max_length=100, blank=True)
    unit_number = models.CharField(max_length=20, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s Technician Profile"

class NeurologistProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='neurologist_profile')
    medical_license = models.CharField(max_length=50, blank=True)
    specialty = models.CharField(max_length=100, blank=True)
    years_of_experience = models.PositiveIntegerField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username}'s Neurologist Profile"

class PatientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    date_of_birth = models.DateField(null=True, blank=True)
    medical_history = models.TextField(blank=True)
    current_medications = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s Patient Profile"