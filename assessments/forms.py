from django import forms
from .models import VitalSigns, NIHSSAssessment, ImagingStudy, LabResult

class VitalSignsForm(forms.ModelForm):
    """Form for recording patient vital signs"""
    class Meta:
        model = VitalSigns
        fields = [
            'blood_pressure_systolic', 'blood_pressure_diastolic',
            'heart_rate', 'respiratory_rate', 'temperature',
            'oxygen_saturation', 'blood_glucose'
        ]

class NIHSSAssessmentForm(forms.ModelForm):
    class Meta:
        model = NIHSSAssessment
        exclude = ['patient', 'assessed_by', 'assessed_at']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add help text to each field
        self.fields['loc'].help_text = "Level of Consciousness: 0=Alert, 1=Drowsy, 2=Stuporous, 3=Coma"
        self.fields['loc_questions'].help_text = "Ask month and age: 0=Both correct, 1=One correct, 2=None correct"
        self.fields['loc_commands'].help_text = "Open/close eyes, grip/release: 0=Both correct, 1=One correct, 2=None correct"
        self.fields['gaze'].help_text = "Horizontal eye movement: 0=Normal, 1=Partial gaze palsy, 2=Complete gaze palsy"
        self.fields['visual_fields'].help_text = "Visual field testing: 0=No loss, 1=Partial hemianopia, 2=Complete hemianopia, 3=Bilateral hemianopia"
        self.fields['facial_palsy'].help_text = "Show teeth, raise eyebrows: 0=Normal, 1=Minor, 2=Partial, 3=Complete"
        self.fields['motor_arm_left'].help_text = "Extend arms 90° (sitting) or 45° (supine) for 10 seconds"
        self.fields['motor_arm_right'].help_text = "Extend arms 90° (sitting) or 45° (supine) for 10 seconds"
        self.fields['motor_leg_left'].help_text = "Hold leg at 30° for 5 seconds"
        self.fields['motor_leg_right'].help_text = "Hold leg at 30° for 5 seconds"
        self.fields['ataxia'].help_text = "Finger-nose and heel-shin tests: 0=Absent, 1=Present in one limb, 2=Present in two limbs"
        self.fields['sensory'].help_text = "Pinprick to face, arm, trunk, leg: 0=Normal, 1=Mild loss, 2=Severe loss"
        self.fields['language'].help_text = "Name items, describe picture, read sentences"
        self.fields['dysarthria'].help_text = "Evaluate speech clarity: 0=Normal, 1=Mild, 2=Severe"
        self.fields['extinction'].help_text = "Double simultaneous stimulation: 0=No abnormality, 1=Mild (one modality), 2=Severe (more than one modality)"
        
        # Add Bootstrap form-control class to all fields
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

class ImagingStudyForm(forms.ModelForm):
    """Form for recording imaging studies"""
    class Meta:
        model = ImagingStudy
        fields = ['study_type', 'findings', 'image_url']
        widgets = {
            'findings': forms.Textarea(attrs={'rows': 4})
        }

class LabResultForm(forms.ModelForm):
    """Form for recording lab results"""
    class Meta:
        model = LabResult
        fields = ['test_name', 'test_value', 'reference_range', 'is_abnormal']