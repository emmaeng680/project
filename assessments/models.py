from django.db import models
from patients.models import Patient
from accounts.models import User

class VitalSigns(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='vital_signs')
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    blood_pressure_systolic = models.PositiveIntegerField()
    blood_pressure_diastolic = models.PositiveIntegerField()
    heart_rate = models.PositiveIntegerField()
    respiratory_rate = models.PositiveIntegerField()
    temperature = models.DecimalField(max_digits=4, decimal_places=1)
    oxygen_saturation = models.PositiveIntegerField()
    blood_glucose = models.PositiveIntegerField(blank=True, null=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Only check thresholds if this is a new vital signs record
        if is_new:
            # Import from consultations
            from consultations.utils import check_vital_signs_thresholds
            check_vital_signs_thresholds(self, self.patient)
    
    def __str__(self):
        return f"Vitals for {self.patient} on {self.recorded_at.strftime('%Y-%m-%d %H:%M')}"
    

    
    
    class Meta:
        ordering = ['-recorded_at']

class NIHSSAssessment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='nihss_assessments')
    assessed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    assessed_at = models.DateTimeField(auto_now_add=True)
    
    # Level of consciousness
    loc = models.PositiveSmallIntegerField(choices=[(0, '0 - Alert'), (1, '1 - Drowsy'), (2, '2 - Stuporous'), (3, '3 - Coma')])
    loc_questions = models.PositiveSmallIntegerField(choices=[(0, '0 - Answers both correctly'), (1, '1 - Answers one correctly'), (2, '2 - Answers none correctly')])
    loc_commands = models.PositiveSmallIntegerField(choices=[(0, '0 - Performs both tasks'), (1, '1 - Performs one task'), (2, '2 - Performs neither')])
    
    # Motor function
    gaze = models.PositiveSmallIntegerField(choices=[(0, '0 - Normal'), (1, '1 - Partial gaze palsy'), (2, '2 - Total gaze palsy')])
    visual_fields = models.PositiveSmallIntegerField(choices=[(0, '0 - No visual loss'), (1, '1 - Partial hemianopia'), (2, '2 - Complete hemianopia'), (3, '3 - Bilateral hemianopia')])
    facial_palsy = models.PositiveSmallIntegerField(choices=[(0, '0 - Normal'), (1, '1 - Minor'), (2, '2 - Partial'), (3, '3 - Complete')])
    
    # Motor arm
    motor_arm_left = models.PositiveSmallIntegerField(choices=[(0, '0 - No drift'), (1, '1 - Drift'), (2, '2 - Can\'t resist gravity'), (3, '3 - No effort against gravity'), (4, '4 - No movement')])
    motor_arm_right = models.PositiveSmallIntegerField(choices=[(0, '0 - No drift'), (1, '1 - Drift'), (2, '2 - Can\'t resist gravity'), (3, '3 - No effort against gravity'), (4, '4 - No movement')])
    
    # Motor leg
    motor_leg_left = models.PositiveSmallIntegerField(choices=[(0, '0 - No drift'), (1, '1 - Drift'), (2, '2 - Can\'t resist gravity'), (3, '3 - No effort against gravity'), (4, '4 - No movement')])
    motor_leg_right = models.PositiveSmallIntegerField(choices=[(0, '0 - No drift'), (1, '1 - Drift'), (2, '2 - Can\'t resist gravity'), (3, '3 - No effort against gravity'), (4, '4 - No movement')])
    
    # Ataxia
    ataxia = models.PositiveSmallIntegerField(choices=[(0, '0 - Absent'), (1, '1 - Present in one limb'), (2, '2 - Present in two limbs')])
    
    # Sensory
    sensory = models.PositiveSmallIntegerField(choices=[(0, '0 - Normal'), (1, '1 - Mild loss'), (2, '2 - Severe loss')])
    
    # Language
    language = models.PositiveSmallIntegerField(choices=[(0, '0 - No aphasia'), (1, '1 - Mild aphasia'), (2, '2 - Severe aphasia'), (3, '3 - Mute')])
    dysarthria = models.PositiveSmallIntegerField(choices=[(0, '0 - Normal'), (1, '1 - Mild'), (2, '2 - Severe')])
    
    # Extinction
    extinction = models.PositiveSmallIntegerField(choices=[(0, '0 - No abnormality'), (1, '1 - Mild'), (2, '2 - Severe')])
    
    # Notes and total score
    notes = models.TextField(blank=True)
    
    def get_total_score(self):
        return sum([
            self.loc, self.loc_questions, self.loc_commands,
            self.gaze, self.visual_fields, self.facial_palsy,
            self.motor_arm_left, self.motor_arm_right,
            self.motor_leg_left, self.motor_leg_right,
            self.ataxia, self.sensory, self.language,
            self.dysarthria, self.extinction
        ])
    
    def __str__(self):
        return f"NIHSS for {self.patient} - Score: {self.get_total_score()}"
    
    class Meta:
        ordering = ['-assessed_at']

class ImagingStudy(models.Model):
    STUDY_TYPES = [
        ('CT', 'CT Scan'),
        ('CTA', 'CT Angiography'),
        ('MRI', 'MRI'),
        ('MRA', 'MR Angiography'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='imaging_studies')
    study_type = models.CharField(max_length=3, choices=STUDY_TYPES)
    performed_at = models.DateTimeField(auto_now_add=True)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    findings = models.TextField()
    image_url = models.URLField(blank=True)
    
    def __str__(self):
        return f"{self.study_type} for {self.patient} on {self.performed_at.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        ordering = ['-performed_at']
        verbose_name_plural = "Imaging Studies"

    # Existing fields...
    image_file = models.FileField(upload_to='imaging_studies/', blank=True, null=True)
    # image_url field still exists for external URLs
    
    def save(self, *args, **kwargs):
        # If image_file is provided but image_url isn't, set the URL from the file
        if self.image_file and not self.image_url:
            self.image_url = self.image_file.url if self.image_file else ''
        super().save(*args, **kwargs)

class LabResult(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='lab_results')
    test_name = models.CharField(max_length=100)
    test_value = models.CharField(max_length=50)
    reference_range = models.CharField(max_length=50)
    is_abnormal = models.BooleanField(default=False)
    recorded_at = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.test_name} for {self.patient}"
    
    class Meta:
        ordering = ['-recorded_at']