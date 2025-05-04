from django.db import models
from patients.models import Patient
from accounts.models import User

class Consultation(models.Model):
    STATUS_CHOICES = [
        ('REQUESTED', 'Requested'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='consultations')
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='requested_consultations')
    neurologist = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='handled_consultations')
    
    requested_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REQUESTED')
    chief_complaint = models.TextField()
    notes = models.TextField(blank=True)
    diagnosis = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    
    def __str__(self):
        return f"Consultation for {self.patient} ({self.status})"
    
    class Meta:
        ordering = ['-requested_at']

class TPARequest(models.Model):
    STATUS_CHOICES = [
        ('REQUESTED', 'Requested'),
        ('APPROVED', 'Approved'),
        ('DENIED', 'Denied'),
    ]
    
    consultation = models.OneToOneField(Consultation, on_delete=models.CASCADE, related_name='tpa_request')
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='tpa_requests')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reviewed_tpa_requests')
    
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REQUESTED')
    justification = models.TextField()
    review_notes = models.TextField(blank=True)
    
    # tPA administration details
    administered = models.BooleanField(default=False)
    administered_at = models.DateTimeField(null=True, blank=True)
    administered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='administered_tpa')
    administration_notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"tPA Request for {self.consultation.patient} ({self.status})"
    
    class Meta:
        ordering = ['-requested_at']
        verbose_name = "tPA Request"
        verbose_name_plural = "tPA Requests"

class Notification(models.Model):
    TYPE_CHOICES = [
        ('CONSULTATION', 'Consultation Update'),
        ('TPA', 'tPA Request Update'),
        ('SYSTEM', 'System Notification'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    created_at = models.DateTimeField(auto_now_add=True)
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=100)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    related_consultation = models.ForeignKey(Consultation, on_delete=models.SET_NULL, null=True, blank=True)
    related_tpa_request = models.ForeignKey(TPARequest, on_delete=models.SET_NULL, null=True, blank=True)
    # Add this field to your Notification model
    related_url = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return f"{self.notification_type} notification for {self.user.username}"
    
    class Meta:
        ordering = ['-created_at']