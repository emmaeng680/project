from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

def home(request):
    """Home view with role-based redirects for authenticated users"""
    if request.user.is_authenticated:
        try:
            # Safely check user roles and redirect
            if hasattr(request.user, 'is_patient') and request.user.is_patient:
                return redirect('patients:dashboard')
            elif hasattr(request.user, 'is_technician') and request.user.is_technician:
                return redirect('consultations:technician_dashboard')
            elif hasattr(request.user, 'is_neurologist') and request.user.is_neurologist:
                return redirect('consultations:neurologist_dashboard')
        except Exception as e:
            # If any error occurs during redirection, log it and stay on home page
            print(f"Error during role-based redirection: {e}")
            messages.warning(request, "An error occurred. Please contact support if this persists.")
    
    # For non-authenticated users or if redirection fails
    return render(request, 'home.html')


@login_required
def dashboard(request):
    """Dashboard with patient statistics"""
    from django.db.models import Count, Avg
    from .models import Patient
    from assessments.models import NIHSSAssessment
    
    # Get counts
    total_patients = Patient.objects.count()
    
    # Get patients registered today
    from django.utils import timezone
    from datetime import timedelta
    today = timezone.now().date()
    patients_today = Patient.objects.filter(registration_date__date=today).count()
    
    # Get gender distribution
    gender_distribution = Patient.objects.values('gender').annotate(count=Count('gender'))
    gender_labels = []
    gender_data = []
    
    for item in gender_distribution:
        if item['gender'] == 'M':
            gender_labels.append('Male')
        elif item['gender'] == 'F':
            gender_labels.append('Female')
        else:
            gender_labels.append('Other')
        gender_data.append(item['count'])
    
    # Get age distribution
    age_ranges = {
        '0-18': 0,
        '19-40': 0,
        '41-60': 0,
        '61-80': 0,
        '81+': 0
    }
    
    for patient in Patient.objects.all():
        if patient.date_of_birth:
            today = timezone.now().date()
            age = today.year - patient.date_of_birth.year
            if today.month < patient.date_of_birth.month or (today.month == patient.date_of_birth.month and today.day < patient.date_of_birth.day):
                age -= 1
                
            if age <= 18:
                age_ranges['0-18'] += 1
            elif age <= 40:
                age_ranges['19-40'] += 1
            elif age <= 60:
                age_ranges['41-60'] += 1
            elif age <= 80:
                age_ranges['61-80'] += 1
            else:
                age_ranges['81+'] += 1
    
    # Get NIHSS score distribution
    try:
        from assessments.models import NIHSSAssessment
        
        # Average NIHSS score
        avg_nihss = NIHSSAssessment.objects.all()
        if avg_nihss.exists():
            # Calculate average score manually
            total_score = 0
            count = 0
            for assessment in avg_nihss:
                total_score += assessment.get_total_score()
                count += 1
            
            avg_nihss_score = round(total_score / count, 1) if count > 0 else 0
        else:
            avg_nihss_score = 0
            
        # NIHSS severity distribution
        severity_distribution = {
            'Minor': 0,
            'Moderate': 0,
            'Severe': 0
        }
        
        for assessment in NIHSSAssessment.objects.all():
            score = assessment.get_total_score()
            if score <= 4:
                severity_distribution['Minor'] += 1
            elif score <= 15:
                severity_distribution['Moderate'] += 1
            else:
                severity_distribution['Severe'] += 1
    except:
        avg_nihss_score = 0
        severity_distribution = {'Minor': 0, 'Moderate': 0, 'Severe': 0}
    
    return render(request, 'patients/dashboard.html', {
        'total_patients': total_patients,
        'patients_today': patients_today,
        'gender_labels': gender_labels,
        'gender_data': gender_data,
        'age_ranges': age_ranges,
        'avg_nihss_score': avg_nihss_score,
        'severity_distribution': severity_distribution
    })