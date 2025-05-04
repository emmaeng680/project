from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from patients.models import Patient
from .models import NIHSSAssessment
from .forms import NIHSSAssessmentForm


@login_required
def perform_nihss(request, patient_id):
    """Perform a new NIHSS assessment for a patient"""
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Check if user has permission (neurologist or technician)
    has_permission = False
    if hasattr(request.user, 'role') and request.user.role in ['NEUROLOGIST', 'TECHNICIAN']:
        has_permission = True
    elif hasattr(request.user, 'is_neurologist') and request.user.is_neurologist:
        has_permission = True
    elif hasattr(request.user, 'is_technician') and request.user.is_technician:
        has_permission = True
    elif request.user.is_superuser or request.user.is_staff:
        has_permission = True
        
    if not has_permission:
        messages.error(request, "You don't have permission to perform NIHSS assessments.")
        return redirect('patients:detail', patient_id=patient_id)
    
    if request.method == 'POST':
        form = NIHSSAssessmentForm(request.POST)
        if form.is_valid():
            assessment = form.save(commit=False)
            assessment.patient = patient
            assessment.assessed_by = request.user
            assessment.save()
            
            # Calculate total score for the message
            total_score = assessment.get_total_score()
            
            messages.success(request, f"NIHSS assessment completed. Total score: {total_score}")
            return redirect('patients:detail', patient_id=patient_id)
    else:
        form = NIHSSAssessmentForm()
    
    return render(request, 'assessments/perform_nihss.html', {
        'form': form,
        'patient': patient
    })





@login_required
def view_nihss_details(request, assessment_id):
    """View details of a specific NIHSS assessment"""
    assessment = get_object_or_404(NIHSSAssessment, id=assessment_id)
    patient = assessment.patient
    
    # Check if user has permission to view
    has_permission = False
    if hasattr(request.user, 'role') and request.user.role in ['NEUROLOGIST', 'TECHNICIAN']:
        has_permission = True
    elif hasattr(request.user, 'is_neurologist') and request.user.is_neurologist:
        has_permission = True
    elif hasattr(request.user, 'is_technician') and request.user.is_technician:
        has_permission = True
    elif request.user.is_superuser or request.user.is_staff:
        has_permission = True
        
    if not has_permission:
        messages.error(request, "You don't have permission to view this assessment.")
        return redirect('home')
    
    total_score = assessment.get_total_score()
    
    # Determine stroke severity based on NIHSS score
    if total_score <= 4:
        severity = "Minor Stroke"
        severity_class = "success"
    elif total_score <= 15:
        severity = "Moderate Stroke"
        severity_class = "warning"
    else:
        severity = "Severe Stroke"
        severity_class = "danger"
    
    return render(request, 'assessments/nihss_details.html', {
        'assessment': assessment,
        'patient': patient,
        'total_score': total_score,
        'severity': severity,
        'severity_class': severity_class
    })


@login_required
def nihss_list(request):
    """View list of all NIHSS assessments (for doctors)"""
    # Check if user is a doctor/neurologist
    is_doctor = False
    if hasattr(request.user, 'role') and request.user.role == 'NEUROLOGIST':
        is_doctor = True
    elif hasattr(request.user, 'is_neurologist') and request.user.is_neurologist:
        is_doctor = True
    elif request.user.is_superuser or request.user.is_staff:
        is_doctor = True
    
    if not is_doctor:
        messages.error(request, "Only neurologists can access the NIHSS assessment list.")
        return redirect('home')
    
    # Get all assessments
    assessments = NIHSSAssessment.objects.all().order_by('-assessed_at')
    
    return render(request, 'assessments/nihss_list.html', {
        'assessments': assessments
    })


@login_required
def doctor_dashboard(request):
    """Dashboard specifically for doctors/neurologists"""
    # Check if user is a doctor/neurologist
    is_doctor = False
    if hasattr(request.user, 'role') and request.user.role == 'NEUROLOGIST':
        is_doctor = True
    elif hasattr(request.user, 'is_neurologist') and request.user.is_neurologist:
        is_doctor = True
    elif request.user.is_superuser or request.user.is_staff:
        is_doctor = True
    
    if not is_doctor:
        messages.error(request, "Only neurologists can access the doctor dashboard.")
        return redirect('home')
    
    from django.db.models import Count, Avg
    from django.utils import timezone
    from datetime import timedelta
    from patients.models import Patient
    from .models import NIHSSAssessment
    
    # Get statistics
    total_assessments = NIHSSAssessment.objects.count()
    
    # Assessments by the current doctor
    doctor_assessments = NIHSSAssessment.objects.filter(assessed_by=request.user).count()
    
    # Get assessments today
    today = timezone.now().date()
    assessments_today = NIHSSAssessment.objects.filter(assessed_at__date=today).count()
    
    # Get NIHSS severity distribution
    severity_counts = {
        'minor': 0,
        'moderate': 0,
        'severe': 0
    }
    
    for assessment in NIHSSAssessment.objects.all():
        score = assessment.get_total_score()
        if score <= 4:
            severity_counts['minor'] += 1
        elif score <= 15:
            severity_counts['moderate'] += 1
        else:
            severity_counts['severe'] += 1
    
    # Recent assessments
    recent_assessments = NIHSSAssessment.objects.all().order_by('-assessed_at')[:10]
    
    # NIHSS assessments by day (last 7 days)
    seven_days_ago = today - timedelta(days=7)
    daily_assessments = []
    
    for i in range(7):
        day = seven_days_ago + timedelta(days=i+1)
        count = NIHSSAssessment.objects.filter(assessed_at__date=day).count()
        daily_assessments.append({
            'day': day.strftime('%a'),
            'count': count
        })
    
    return render(request, 'assessments/doctor_dashboard.html', {
        'total_assessments': total_assessments,
        'doctor_assessments': doctor_assessments,
        'assessments_today': assessments_today,
        'severity_counts': severity_counts,
        'recent_assessments': recent_assessments,
        'daily_assessments': daily_assessments,
    })

