from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from .models import Patient
from .forms import PatientRegistrationForm, ResetAccessCodeForm

def patient_access(request):
    """View for patients to access their records using an access code"""
    if request.method == 'POST':
        access_code = request.POST.get('access_code', '').strip().upper()
        
        if not access_code:
            messages.error(request, "Please enter your access code.")
            return redirect('patients:dashboard')  # Redirect to dashboard which has the form
        
        try:
            patient = Patient.objects.get(access_code=access_code)
            
            # Check if code is expired (if you're using expiry)
            if hasattr(patient, 'access_code_expiry') and patient.access_code_expiry and patient.access_code_expiry < timezone.now():
                messages.error(request, "Your access code has expired. Please contact your healthcare provider for a new code.")
                return redirect('patients:dashboard')
            
            # Store patient ID in session
            request.session['patient_id'] = patient.id
            request.session['patient_access_verified'] = True
            request.session['patient_access_time'] = timezone.now().isoformat()
            
            messages.success(request, f"Welcome {patient.first_name}! You can now view your medical information.")
            return redirect('patients:dashboard')  # Redirect to dashboard with verified session
            
        except Patient.DoesNotExist:
            messages.error(request, "Invalid access code. Please check and try again.")
            return redirect('patients:dashboard')
    
    # If GET request, redirect to dashboard with form
    return redirect('patients:dashboard')

@login_required
def dashboard(request):
    """Dashboard for patients and access point"""
    # If accessing via access code (not logged in)
    if request.session.get('patient_access_verified') and request.session.get('patient_id'):
        patient_id = request.session.get('patient_id')
        patient = get_object_or_404(Patient, id=patient_id)
        
        # For security, check if the session is too old (e.g., 30 minutes)
        access_time = request.session.get('patient_access_time')
        if access_time:
            access_time = timezone.datetime.fromisoformat(access_time)
            if (timezone.now() - access_time).total_seconds() > 1800:  # 30 minutes
                # Clear session and redirect to login
                request.session.flush()
                messages.info(request, "Your session has expired for security reasons. Please enter your access code again.")
                return render(request, 'patients/dashboard.html')
        
        # Get patient's consultations, assessments, etc.
        try:
            from consultations.models import Consultation
            consultations = Consultation.objects.filter(patient=patient).order_by('-requested_at')
        except Exception as e:
            print(f"Error fetching consultations: {e}")
            consultations = []
        
        try:
            from assessments.models import NIHSSAssessment, VitalSigns
            assessments = NIHSSAssessment.objects.filter(patient=patient).order_by('-assessed_at')
            vital_signs = VitalSigns.objects.filter(patient=patient).order_by('-recorded_at')
        except Exception as e:
            print(f"Error fetching assessments: {e}")
            assessments = []
            vital_signs = []
        
        # Return the dashboard with patient data
        return render(request, 'patients/dashboard.html', {
            'patient': patient,
            'consultations': consultations[:5],
            'assessments': assessments[:5],
            'vital_signs': vital_signs[:5],
        })
    
    # If this is a logged-in user viewing their dashboard
    if request.user.is_authenticated:
        user = request.user
        
        if hasattr(user, 'is_patient') and user.is_patient and hasattr(user, 'patient_record'):
            patient = user.patient_record
            # Get consultations, assessments for the patient
            consultations = patient.consultations.order_by('-requested_at') if hasattr(patient, 'consultations') else []
            assessments = patient.nihss_assessments.order_by('-assessed_at') if hasattr(patient, 'nihss_assessments') else []
            vital_signs = patient.vital_signs.order_by('-recorded_at') if hasattr(patient, 'vital_signs') else []
            
            return render(request, 'patients/dashboard.html', {
                'patient': patient,
                'consultations': consultations[:5],
                'assessments': assessments[:5],
                'vital_signs': vital_signs[:5],
            })
    
    # For non-patients or patients without a record - show the form
    return render(request, 'patients/dashboard.html')

@login_required
def register_patient(request):
    """Register a new patient - for technicians only"""
    # Only technicians should be able to register patients
    is_technician = request.user.role == 'TECHNICIAN' if hasattr(request.user, 'role') else False
    if hasattr(request.user, 'is_technician'):
        is_technician = request.user.is_technician
    
    if not is_technician:
        from django.contrib import messages
        messages.error(request, "Only technicians can register patients.")
        return redirect('home')
    
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            # Save the form but don't commit to database yet
            patient = form.save(commit=False)
            patient.registered_by = request.user
            
            # Generate an access code for the patient
            if hasattr(patient, 'generate_access_code'):
                patient.access_code = patient.generate_access_code()
            
            patient.save()
            
            # Process vital signs if they are provided
            bp_systolic = request.POST.get('blood_pressure_systolic')
            bp_diastolic = request.POST.get('blood_pressure_diastolic')
            heart_rate = request.POST.get('heart_rate')
            resp_rate = request.POST.get('respiratory_rate')
            temp = request.POST.get('temperature')
            o2_sat = request.POST.get('oxygen_saturation')
            glucose = request.POST.get('blood_glucose')
            
            # Check if we have enough vital sign data to create a record
            if bp_systolic and bp_diastolic and heart_rate and resp_rate and temp and o2_sat:
                try:
                    from assessments.models import VitalSigns
                    vs = VitalSigns(
                        patient=patient,
                        recorded_by=request.user,
                        blood_pressure_systolic=int(bp_systolic),
                        blood_pressure_diastolic=int(bp_diastolic),
                        heart_rate=int(heart_rate),
                        respiratory_rate=int(resp_rate),
                        temperature=float(temp),
                        oxygen_saturation=int(o2_sat),
                        blood_glucose=int(glucose) if glucose else None
                    )
                    vs.save()
                    print(f"Created vital signs record for {patient}")
                except Exception as e:
                    print(f"Error creating vital signs: {e}")

            # Process CT scan upload
            if 'ct_scan' in request.FILES:
                try:
                    from assessments.models import ImagingStudy
                    ct_scan = ImagingStudy(
                        patient=patient,
                        study_type='CT',
                        performed_by=request.user,
                        findings='CT scan uploaded during registration',
                        # Your model doesn't have an 'image' field, but 'image_url' field
                        # Since this is a file upload, we'd need to save it somewhere and store the URL
                        # This is where you'd implement file upload handling
                    )
                    ct_scan.save()
                    # Handle the file upload
                    # Example: save_file_and_update_url(request.FILES['ct_scan'], ct_scan)
                except Exception as e:
                    print(f"Error creating CT scan record: {e}")

            # Process MRI scan upload
            if 'mri_scan' in request.FILES:
                try:
                    from assessments.models import ImagingStudy
                    mri_scan = ImagingStudy(
                        patient=patient,
                        study_type='MRI',
                        performed_by=request.user,
                        findings='MRI scan uploaded during registration',
                        # Handle the file upload similarly to CT scan
                    )
                    mri_scan.save()
                except Exception as e:
                    print(f"Error creating MRI scan record: {e}")

            # Process lab results upload
            if 'lab_results' in request.FILES:
                try:
                    from assessments.models import LabResult
                    lab_result = LabResult(
                        patient=patient,
                        test_name='Initial Lab Results',
                        test_value='See uploaded document',
                        reference_range='N/A',
                        is_abnormal=False,
                        recorded_by=request.user
                    )
                    lab_result.save()
                    # Handle file upload for lab results
                except Exception as e:
                    print(f"Error creating lab result record: {e}")
            
            from django.contrib import messages
            messages.success(request, f"Patient {patient.first_name} {patient.last_name} has been registered successfully.")
            if hasattr(patient, 'access_code') and patient.access_code:
                messages.info(request, f"Patient access code: {patient.access_code}")
            
            # Redirect to the patient detail page
            return redirect('patients:detail', patient_id=patient.id)
        else:
            from django.contrib import messages
            messages.error(request, "There was an error in your form submission. Please check the fields below.")
    else:
        form = PatientRegistrationForm()
    
    return render(request, 'patients/register_patient.html', {'form': form})

@login_required
def patient_list(request):
    """List all patients with search functionality"""
    # Check permissions
    if not (hasattr(request.user, 'is_technician') and request.user.is_technician or 
            hasattr(request.user, 'is_neurologist') and request.user.is_neurologist):
        messages.error(request, "You don't have permission to view patient list.")
        return redirect('home')
    
    # Get the search query from the request
    search_query = request.GET.get('q', '')
    
    # Check if this is for creating a consultation
    action = request.GET.get('action', '')
    
    # Filter patients based on search query if provided
    if search_query:
        patients = Patient.objects.filter(
            Q(first_name__icontains=search_query) | 
            Q(last_name__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(medical_history__icontains=search_query)
        )
        
        # Add a flash message for search results
        patient_count = patients.count()
        if patient_count == 0:
            messages.info(request, f"No patients found matching '{search_query}'")
        else:
            messages.info(request, f"Found {patient_count} patient(s) matching '{search_query}'")
    else:
        # No search query, return all patients
        patients = Patient.objects.all()
    
    # Order by registration date (newest first) or created_at if it exists
    try:
        patients = patients.order_by('-created_at')
    except:
        try:
            patients = patients.order_by('-registration_date')
        except:
            pass  # No ordering if neither field exists
    
    # Render the list.html template (not patient_list.html)
    return render(request, 'patients/patient_list.html', {
        'patients': patients,
        'search_query': search_query,
        'action': action
    })

@login_required
def patient_detail(request, patient_id):
    """View detailed patient information"""
    from django.shortcuts import get_object_or_404
    from .models import Patient
    from assessments.models import VitalSigns, NIHSSAssessment, ImagingStudy, LabResult
    
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Check permissions
    has_permission = False
    if hasattr(request.user, 'role') and request.user.role == 'TECHNICIAN':
        has_permission = True
    elif hasattr(request.user, 'role') and request.user.role == 'NEUROLOGIST':
        has_permission = True
    elif hasattr(request.user, 'is_technician') and request.user.is_technician:
        has_permission = True
    elif hasattr(request.user, 'is_neurologist') and request.user.is_neurologist:
        has_permission = True
    elif hasattr(request.user, 'is_staff') and request.user.is_staff:
        has_permission = True
    elif request.user.is_superuser:
        has_permission = True
    
    if not has_permission:
        from django.contrib import messages
        messages.error(request, "You don't have permission to view this patient's details.")
        return redirect('home')
    
    # Calculate patient age
    patient_age = None
    if patient.date_of_birth:
        from django.utils import timezone
        today = timezone.now().date()
        patient_age = today.year - patient.date_of_birth.year
        if today.month < patient.date_of_birth.month or (
            today.month == patient.date_of_birth.month and today.day < patient.date_of_birth.day
        ):
            patient_age -= 1
    
    # Get the related data - note we're using the correct related_name from your models
    try:
        vital_signs = patient.vital_signs.all().order_by('-recorded_at')
    except Exception as e:
        print(f"Error fetching vital signs: {e}")
        vital_signs = []

    try:
        nihss_assessments = patient.nihss_assessments.all().order_by('-assessed_at')
    except Exception as e:
        print(f"Error fetching NIHSS assessments: {e}")
        nihss_assessments = []

    try:
        imaging_studies = patient.imaging_studies.all().order_by('-performed_at')
    except Exception as e:
        print(f"Error fetching imaging studies: {e}")
        imaging_studies = []

    try:
        lab_results = patient.lab_results.all().order_by('-recorded_at')
    except Exception as e:
        print(f"Error fetching lab results: {e}")
        lab_results = []

    # Debug information
    print(f"Patient: {patient.first_name} {patient.last_name}")
    print(f"Vital Signs: {vital_signs.count()}")
    print(f"NIHSS Assessments: {nihss_assessments.count()}")
    print(f"Imaging Studies: {imaging_studies.count()}")
    print(f"Lab Results: {lab_results.count()}")
    
    return render(request, 'patients/patient_detail.html', {
        'patient': patient,
        'patient_age': patient_age,
        'vital_signs': vital_signs,
        'nihss_assessments': nihss_assessments,
        'imaging_studies': imaging_studies,
        'lab_results': lab_results,
    })

# New views for patient portal functionality

@login_required
def reset_patient_access(request, patient_id):
    """Reset a patient's access code"""
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Check permissions
    has_permission = False
    if hasattr(request.user, 'role') and request.user.role == 'TECHNICIAN':
        has_permission = True
    elif hasattr(request.user, 'is_technician') and request.user.is_technician:
        has_permission = True
    elif request.user.is_staff or request.user.is_superuser:
        has_permission = True
    
    if not has_permission:
        messages.error(request, "You don't have permission to reset patient access codes.")
        return redirect('patients:detail', patient_id=patient.id)
    
    if request.method == 'POST':
        form = ResetAccessCodeForm(request.POST)
        if form.is_valid() and form.cleaned_data['confirm']:
            if hasattr(patient, 'reset_access_code'):
                new_code = patient.reset_access_code()
                messages.success(request, f"Access code reset successfully. New code: {new_code}")
            else:
                # If reset_access_code method doesn't exist, manually generate and save a code
                from django.utils.crypto import get_random_string
                patient.access_code = get_random_string(8).upper()
                patient.save()
                messages.success(request, f"Access code reset successfully. New code: {patient.access_code}")
            
            return redirect('patients:detail', patient_id=patient.id)
    else:
        form = ResetAccessCodeForm()
    
    return render(request, 'patients/reset_access_code.html', {
        'form': form,
        'patient': patient
    })

# def patient_access(request):
    """View for patients to access their records using an access code"""
    if request.method == 'POST':
        access_code = request.POST.get('access_code', '').strip().upper()
        
        if not access_code:
            messages.error(request, "Please enter your access code.")
            return render(request, 'patients/patient_access.html')
        
        try:
            patient = Patient.objects.get(access_code=access_code)
            
            # Check if code is expired (if you're using expiry)
            if hasattr(patient, 'access_code_expiry') and patient.access_code_expiry and patient.access_code_expiry < timezone.now():
                messages.error(request, "Your access code has expired. Please contact your healthcare provider for a new code.")
                return render(request, 'patients/patient_access.html')
            
            # Store patient ID in session
            request.session['patient_id'] = patient.id
            request.session['patient_access_verified'] = True
            request.session['patient_access_time'] = timezone.now().isoformat()
            
            messages.success(request, f"Welcome {patient.first_name}! You can now view your medical information.")
            return redirect('patients:patient_dashboard')
            
        except Patient.DoesNotExist:
            messages.error(request, "Invalid access code. Please check and try again.")
            return render(request, 'patients/patient_access.html')
    
    return render(request, 'patients/patient_access.html')

def patient_dashboard(request):
    """Patient dashboard showing their medical information"""
    # Check if patient is verified
    if not request.session.get('patient_access_verified'):
        messages.error(request, "Please enter your access code to view your medical information.")
        return redirect('patients:patient_access')
    
    # Get patient using session ID
    patient_id = request.session.get('patient_id')
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Get patient's consultations - adapt to your related_name if different
    try:
        from consultations.models import Consultation
        consultations = Consultation.objects.filter(patient=patient).order_by('-requested_at')
    except Exception as e:
        print(f"Error fetching consultations: {e}")
        consultations = []
    
    # Get patient's assessments
    try:
        from assessments.models import NIHSSAssessment, VitalSigns
        assessments = NIHSSAssessment.objects.filter(patient=patient).order_by('-assessed_at')
        vital_signs = VitalSigns.objects.filter(patient=patient).order_by('-recorded_at')
    except Exception as e:
        print(f"Error fetching assessments: {e}")
        assessments = []
        vital_signs = []
    
    # Get patient's tPA requests if applicable
    try:
        from consultations.models import TPARequest
        tpa_requests = TPARequest.objects.filter(consultation__patient=patient).order_by('-requested_at')
    except Exception as e:
        print(f"Error fetching tPA requests: {e}")
        tpa_requests = []
    
    # For security, check if the session is too old (e.g., 30 minutes)
    access_time = request.session.get('patient_access_time')
    if access_time:
        access_time = timezone.datetime.fromisoformat(access_time)
        if (timezone.now() - access_time).total_seconds() > 1800:  # 30 minutes
            # Clear session and redirect to login
            request.session.flush()
            messages.info(request, "Your session has expired for security reasons. Please enter your access code again.")
            return redirect('patients:patient_access')
    
    return render(request, 'patients/patient_dashboard.html', {
        'patient': patient,
        'consultations': consultations,
        'assessments': assessments,
        'vital_signs': vital_signs,
        'tpa_requests': tpa_requests,
    })

def patient_logout(request):
    """Log out the patient by clearing their session"""
    request.session.flush()
    messages.info(request, "You have been logged out successfully.")
    return redirect('patients:patient_access')


@login_required
def reset_patient_access(request, patient_id):
    """Reset a patient's access code"""
    patient = get_object_or_404(Patient, id=patient_id)
    
    if not (request.user.is_staff or request.user.role == 'TECHNICIAN'):
        messages.error(request, "You don't have permission to reset patient access codes.")
        return redirect('patients:detail', patient_id=patient.id)
    
    if request.method == 'POST':
        form = ResetAccessCodeForm(request.POST)
        if form.is_valid() and form.cleaned_data['confirm']:
            new_code = patient.reset_access_code()
            messages.success(request, f"Access code reset successfully. New code: {new_code}")
            return redirect('patients:detail', patient_id=patient.id)
    else:
        form = ResetAccessCodeForm()
    
    return render(request, 'patients/reset_access_code.html', {
        'form': form,
        'patient': patient
    })