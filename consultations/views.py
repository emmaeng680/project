from django.db.models import Q
from django.http import HttpResponseRedirect
from assessments.models import VitalSigns
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from patients.models import Patient
from .models import Consultation, TPARequest, Notification
from .forms import (ConsultationRequestForm, ConsultationCompleteForm, 
                   TPARequestForm, TPAReviewForm, TPAAdministrationForm)




@login_required
def technician_dashboard(request):
    """Dashboard for technicians showing their consultations and patients"""
    # Verify user is a technician
    is_technician = request.user.role == 'TECHNICIAN' if hasattr(request.user, 'role') else False
    if hasattr(request.user, 'is_technician') and request.user.is_technician:
        is_technician = True
    
    if not (is_technician or request.user.is_superuser):
        messages.error(request, "You don't have permission to access the technician dashboard.")
        return redirect('home')
    
    # Get active consultations requested by this technician
    active_consultations = Consultation.objects.filter(
        requested_by=request.user
    ).exclude(
        status='CANCELLED'
    ).order_by('-requested_at')[:7]  # Show top 7 consultations
    
    # Get recent patients registered by this technician
    from patients.models import Patient
    recent_patients = Patient.objects.filter(
        registered_by=request.user
    ).order_by('-created_at')[:5]
    
    # Get pending tPA requests made by this technician
    pending_tpa_requests = TPARequest.objects.filter(
        requested_by=request.user,
        status='REQUESTED'
    ).order_by('-requested_at')
    
    return render(request, 'consultations/technician_dashboard.html', {
        'active_consultations': active_consultations,
        'recent_patients': recent_patients,
        'pending_tpa_requests': pending_tpa_requests,
    })

@login_required
def neurologist_dashboard(request):
    """Dashboard for neurologists"""
    if not request.user.is_neurologist:
        messages.error(request, "You don't have permission to access the neurologist dashboard.")
        return redirect('home')
    
    # Get data for the neurologist dashboard
    pending_consultations = Consultation.objects.filter(
        status='REQUESTED'
    ).order_by('-requested_at')
    
    active_consultations = Consultation.objects.filter(
        status='IN_PROGRESS',
        neurologist=request.user
    ).order_by('-started_at')
    
    pending_tpa_requests = TPARequest.objects.filter(
        status='REQUESTED'
    ).order_by('-requested_at')
    
    return render(request, 'consultations/neurologist_dashboard.html', {
        'pending_consultations': pending_consultations,
        'active_consultations': active_consultations,
        'pending_tpa_requests': pending_tpa_requests,
    })



@login_required
def request_consultation(request, patient_id):
    """Request a new consultation for a patient"""
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Only technicians can request consultations
    is_technician = request.user.role == 'TECHNICIAN' if hasattr(request.user, 'role') else False
    if hasattr(request.user, 'is_technician') and request.user.is_technician:
        is_technician = True
    
    if not is_technician and not request.user.is_superuser:
        messages.error(request, "Only technicians can request consultations.")
        return redirect('patients:detail', patient_id=patient_id)
    
    if request.method == 'POST':
        # Handle direct form submission from the modal
        chief_complaint = request.POST.get('chief_complaint')
        notes = request.POST.get('notes', '')
        
        if not chief_complaint:
            messages.error(request, "Chief complaint is required.")
            return redirect('patients:list')
        
        # Create the consultation
        consultation = Consultation.objects.create(
            patient=patient,
            requested_by=request.user,
            chief_complaint=chief_complaint,
            notes=notes,
            status='REQUESTED'
        )
        
        # Create notification for neurologists
        from accounts.models import User
        neurologists = User.objects.filter(role='NEUROLOGIST')
        for neurologist in neurologists:
            Notification.objects.create(
                user=neurologist,
                notification_type='CONSULTATION',
                title='New Consultation Request',
                message=f'New consultation requested for {patient.first_name} {patient.last_name}',
                related_consultation=consultation
            )
        
        messages.success(request, "Consultation request submitted successfully.")
        return redirect('consultations:detail', consultation_id=consultation.id)
    else:
        # If GET request, show the form page
        form = ConsultationRequestForm()
    
    return render(request, 'consultations/request_consultation.html', {
        'form': form,
        'patient': patient,
    })

@login_required
def consultation_detail(request, consultation_id):
    """View consultation details"""
    consultation = get_object_or_404(Consultation, id=consultation_id)
    
    # Check permissions
    is_neurologist = request.user.role == 'NEUROLOGIST' if hasattr(request.user, 'role') else False
    is_technician = request.user.role == 'TECHNICIAN' if hasattr(request.user, 'role') else False
    
    if hasattr(request.user, 'is_neurologist') and request.user.is_neurologist:
        is_neurologist = True
    if hasattr(request.user, 'is_technician') and request.user.is_technician:
        is_technician = True
    
    if not (is_neurologist or is_technician or request.user.is_superuser or 
            request.user == consultation.requested_by or 
            request.user == consultation.neurologist):
        messages.error(request, "You don't have permission to view this consultation.")
        return redirect('home')
    
    # Check for tPA request
    try:
        tpa_request = consultation.tpa_request
    except:
        tpa_request = None
    
    # Mark related notifications as read
    if request.user.is_authenticated:
        Notification.objects.filter(
            user=request.user,
            related_consultation=consultation,
            is_read=False
        ).update(is_read=True)
    
    return render(request, 'consultations/consultation_detail.html', {
        'consultation': consultation,
        'patient': consultation.patient,
        'tpa_request': tpa_request,
        'is_neurologist': is_neurologist,
        'is_technician': is_technician,
    })


@login_required
def accept_consultation(request, consultation_id):
    """Allow a neurologist to accept a consultation and mark it as in-progress"""
    consultation = get_object_or_404(Consultation, id=consultation_id)
    
    # Verify user is a neurologist
    is_neurologist = False
    if hasattr(request.user, 'role'):
        is_neurologist = request.user.role == 'NEUROLOGIST'
    elif hasattr(request.user, 'is_neurologist'):
        is_neurologist = request.user.is_neurologist
    
    if not (is_neurologist or request.user.is_superuser):
        messages.error(request, "Only neurologists can accept consultations.")
        return redirect('consultations:detail', consultation_id=consultation_id)
    
    # Ensure consultation is in REQUESTED state
    if consultation.status != 'REQUESTED':
        messages.error(request, "This consultation cannot be accepted because it's not in a requested state.")
        return redirect('consultations:detail', consultation_id=consultation_id)
    
    # Accept the consultation
    consultation.neurologist = request.user
    consultation.status = 'IN_PROGRESS'
    consultation.started_at = timezone.now()
    consultation.save()
    
    # Create notification for the technician
    if consultation.requested_by:
        Notification.objects.create(
            user=consultation.requested_by,
            notification_type='CONSULTATION',
            title='Consultation Accepted',
            message=f'Your consultation request for {consultation.patient.first_name} {consultation.patient.last_name} has been accepted by {request.user.get_full_name() or request.user.username}',
            related_consultation=consultation
        )
    
    messages.success(request, "Consultation successfully accepted.")
    return redirect('consultations:detail', consultation_id=consultation_id)

@login_required
def request_tpa(request, consultation_id):
    """Request tPA administration for a patient"""
    if not request.user.is_technician:
        messages.error(request, "Only technicians can request tPA administration.")
        return redirect('home')
    
    consultation = get_object_or_404(Consultation, id=consultation_id)
    
    # Check if tPA request already exists
    try:
        tpa_request = consultation.tpa_request
        messages.error(request, "A tPA request already exists for this consultation.")
        return redirect('consultations:detail', consultation_id=consultation.id)
    except TPARequest.DoesNotExist:
        pass
    
    if request.method == 'POST':
        form = TPARequestForm(request.POST)
        if form.is_valid():
            tpa_request = form.save(commit=False)
            tpa_request.consultation = consultation
            tpa_request.requested_by = request.user
            tpa_request.status = 'REQUESTED'
            tpa_request.save()
            
            messages.success(request, "tPA request has been submitted.")
            return redirect('consultations:detail', consultation_id=consultation.id)
    else:
        form = TPARequestForm()
    
    return render(request, 'consultations/request_tpa.html', {
        'form': form,
        'consultation': consultation,
    })

@login_required
def review_tpa(request, tpa_id):
    """Review tPA request - for neurologists only"""
    if not request.user.is_neurologist:
        messages.error(request, "Only neurologists can review tPA requests.")
        return redirect('home')
    
    tpa_request = get_object_or_404(TPARequest, id=tpa_id)
    consultation = tpa_request.consultation
    
    if request.method == 'POST':
        form = TPAReviewForm(request.POST, instance=tpa_request)
        if form.is_valid():
            tpa_request = form.save(commit=False)
            tpa_request.reviewed_by = request.user
            tpa_request.reviewed_at = timezone.now()
            tpa_request.save()
            
            # Create notification for the technician and patient
            Notification.objects.create(
                user=tpa_request.requested_by,
                notification_type='TPA',
                title='tPA Request Reviewed',
                message=f'tPA request for {consultation.patient.get_full_name()} has been {tpa_request.status.lower()}.',
                related_tpa_request=tpa_request
            )
            
            if consultation.patient.user_account:
                Notification.objects.create(
                    user=consultation.patient.user_account,
                    notification_type='TPA',
                    title='tPA Request Update',
                    message=f'Your tPA request has been {tpa_request.status.lower()} by Dr. {request.user.get_full_name()}.',
                    related_tpa_request=tpa_request
                )
            
            messages.success(request, "tPA request has been reviewed.")
            return redirect('consultations:detail', consultation_id=consultation.id)
    else:
        form = TPAReviewForm(instance=tpa_request)
    
    return render(request, 'consultations/review_tpa.html', {
        'form': form,
        'tpa_request': tpa_request,
        'consultation': consultation,
    })

@login_required
def administer_tpa(request, tpa_id):
    """Record tPA administration - for technicians only"""
    if not request.user.is_technician:
        messages.error(request, "Only technicians can record tPA administration.")
        return redirect('home')
    
    tpa_request = get_object_or_404(TPARequest, id=tpa_id)
    consultation = tpa_request.consultation
    
    if tpa_request.status != 'APPROVED':
        messages.error(request, "Cannot administer tPA that has not been approved.")
        return redirect('consultations:detail', consultation_id=consultation.id)
    
    if request.method == 'POST':
        form = TPAAdministrationForm(request.POST, instance=tpa_request)
        if form.is_valid():
            tpa_request = form.save(commit=False)
            if tpa_request.administered:
                tpa_request.administered_by = request.user
                tpa_request.administered_at = timezone.now()
            tpa_request.save()
            
            # Create notification for the patient
            if consultation.patient.user_account:
                Notification.objects.create(
                    user=consultation.patient.user_account,
                    notification_type='TPA',
                    title='tPA Administered',
                    message='tPA has been administered for your stroke treatment.',
                    related_tpa_request=tpa_request
                )
            
            messages.success(request, "tPA administration has been recorded.")
            return redirect('consultations:detail', consultation_id=consultation.id)
    else:
        form = TPAAdministrationForm(instance=tpa_request)
    
    return render(request, 'consultations/administer_tpa.html', {
        'form': form,
        'tpa_request': tpa_request,
        'consultation': consultation,
    })

@login_required
def notification_list(request):
    """View user notifications"""
    notifications = request.user.notifications.order_by('-created_at')
    
    # Mark all as read when viewed
    unread = notifications.filter(is_read=False)
    unread.update(is_read=True)
    
    return render(request, 'consultations/notification_list.html', {
        'notifications': notifications
    })

@login_required
def notification_detail(request, notification_id):
    """View a single notification"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    
    # Mark as read
    if not notification.is_read:
        notification.is_read = True
        notification.save()
    
    # Determine related object to display
    related_object = None
    if notification.related_consultation:
        related_object = notification.related_consultation
    elif notification.related_tpa_request:
        related_object = notification.related_tpa_request
    
    return render(request, 'consultations/notification_detail.html', {
        'notification': notification,
        'related_object': related_object
    })

@login_required
def technician_dashboard(request):
    """Dashboard view for technicians."""
    # Check if user is a technician
    if not (hasattr(request.user, 'is_technician') and request.user.is_technician or 
            hasattr(request.user, 'role') and request.user.role == 'TECHNICIAN'):
        messages.error(request, "You don't have permission to access the technician dashboard.")
        return redirect('home')
    
    # Get recent consultations
    active_consultations = Consultation.objects.filter(
        status__in=['REQUESTED', 'IN_PROGRESS']
    ).order_by('-requested_at')[:5]
    
    # Get recent patients
    recent_patients = Patient.objects.all().order_by('-registration_date' if hasattr(Patient, 'registration_date') else '-id')[:5]
    
    # Get pending tPA requests
    pending_tpa_requests = TPARequest.objects.filter(
        status='REQUESTED'
    ).order_by('-requested_at')[:5]
    
    # Get notification count
    notification_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    return render(request, 'consultations/technician_dashboard.html', {
        'active_consultations': active_consultations,
        'recent_patients': recent_patients,
        'pending_tpa_requests': pending_tpa_requests,
        'notification_count': notification_count
    })


# @login_required
# def neurologist_dashboard(request):
#     return render(request, 'consultations/neurologist_dashboard.html')


@login_required
def neurologist_dashboard(request):
    """Dashboard for neurologists showing pending consultations and tPA requests"""
    # Verify user is a neurologist
    is_neurologist = request.user.role == 'NEUROLOGIST' if hasattr(request.user, 'role') else False
    if hasattr(request.user, 'is_neurologist') and request.user.is_neurologist:
        is_neurologist = True
    
    if not (is_neurologist or request.user.is_superuser):
        messages.error(request, "You don't have permission to access the neurologist dashboard.")
        return redirect('home')
    
    # Get pending consultations (no neurologist assigned or assigned to this neurologist)
    pending_consultations = Consultation.objects.filter(
        status='REQUESTED',
        neurologist=None
    ).order_by('-requested_at')[:10]
    
    # Get in-progress consultations assigned to this neurologist
    in_progress_consultations = Consultation.objects.filter(
        status='IN_PROGRESS',
        neurologist=request.user
    ).order_by('-started_at')[:10]
    
    # Get recently completed consultations by this neurologist
    recent_completed_consultations = Consultation.objects.filter(
        status='COMPLETED', 
        neurologist=request.user
    ).order_by('-completed_at')[:5]
    
    # Get pending tPA requests
    pending_tpa_requests = TPARequest.objects.filter(
        status='REQUESTED',
        consultation__neurologist=request.user
    ) | TPARequest.objects.filter(
        status='REQUESTED',
        consultation__neurologist=None
    ).order_by('-requested_at')
    
    # Get counts for the dashboard stats
    pending_consultations_count = Consultation.objects.filter(
        status='REQUESTED', 
        neurologist=None
    ).count()
    
    in_progress_consultations_count = Consultation.objects.filter(
        status='IN_PROGRESS', 
        neurologist=request.user
    ).count()
    
    pending_tpa_count = pending_tpa_requests.count()
    
    return render(request, 'consultations/neurologist_dashboard.html', {
        'pending_consultations': pending_consultations,
        'in_progress_consultations': in_progress_consultations,
        'recent_completed_consultations': recent_completed_consultations,
        'pending_tpa_requests': pending_tpa_requests,
        'pending_consultations_count': pending_consultations_count,
        'in_progress_consultations_count': in_progress_consultations_count,
        'pending_tpa_count': pending_tpa_count,
    })

# @login_required
# def notifications(request):
#     return render(request, 'consultations/notifications.html', {'notifications': []})

@login_required
def notifications(request):
    """View system notifications for the current user"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Mark all as read if requested
    if request.GET.get('mark_all_read'):
        notifications.update(is_read=True)
        messages.success(request, "All notifications marked as read")
        return redirect('consultations:notifications')
    
    # Mark one as read if requested
    if request.GET.get('mark_read'):
        try:
            notif_id = int(request.GET.get('mark_read'))
            notif = Notification.objects.get(id=notif_id, user=request.user)
            notif.is_read = True
            notif.save()
            messages.success(request, "Notification marked as read")
            
            # If there's a next parameter, redirect there
            next_url = request.GET.get('next')
            if next_url:
                return HttpResponseRedirect(next_url)
        except (ValueError, Notification.DoesNotExist):
            messages.error(request, "Notification not found")
        
        return redirect('consultations:notifications')
    
    # View notification and redirect to related URL if provided
    if request.GET.get('view'):
        try:
            notif_id = int(request.GET.get('view'))
            notif = Notification.objects.get(id=notif_id, user=request.user)
            
            # Mark as read
            notif.is_read = True
            notif.save()
            
            # Redirect to related content if available
            if notif.related_consultation:
                return redirect('consultations:detail', consultation_id=notif.related_consultation.id)
            elif notif.related_tpa_request:
                return redirect('consultations:detail', consultation_id=notif.related_tpa_request.consultation.id)
            elif notif.related_url:
                return HttpResponseRedirect(notif.related_url)
            
            messages.info(request, "Viewed notification: " + notif.title)
        except (ValueError, Notification.DoesNotExist):
            messages.error(request, "Notification not found")
            
    unread_count = notifications.filter(is_read=False).count()
    
    return render(request, 'consultations/notifications.html', {
        'notifications': notifications,
        'unread_count': unread_count
    })


@login_required
def update_consultation(request, consultation_id):
    """Update an existing consultation"""
    consultation = get_object_or_404(Consultation, id=consultation_id)
    
    # Check if user has permission to update
    is_authorized = False
    if request.user == consultation.neurologist:
        is_authorized = True
    elif request.user.is_superuser:
        is_authorized = True
    
    if not is_authorized:
        messages.error(request, "You don't have permission to update this consultation.")
        return redirect('consultations:detail', consultation_id=consultation_id)
    
    if request.method == 'POST':
        if 'complete' in request.POST:
            # Use the complete consultation form
            form = ConsultationCompleteForm(request.POST, instance=consultation)
            if form.is_valid():
                consultation = form.save(commit=False)
                consultation.status = 'COMPLETED'
                consultation.completed_at = timezone.now()
                consultation.save()
                
                # Create notification for technician
                if consultation.requested_by:
                    Notification.objects.create(
                        user=consultation.requested_by,
                        notification_type='CONSULTATION',
                        title='Consultation Completed',
                        message=f'Consultation for {consultation.patient.first_name} {consultation.patient.last_name} has been completed.',
                        related_consultation=consultation
                    )
                
                messages.success(request, "Consultation completed successfully.")
                return redirect('consultations:detail', consultation_id=consultation_id)
        else:
            # Use the update status form
            form = ConsultationUpdateForm(request.POST, instance=consultation)
            if form.is_valid():
                consultation = form.save(commit=False)
                
                # Set started_at if transitioning to IN_PROGRESS
                if consultation.status == 'IN_PROGRESS' and not consultation.started_at:
                    consultation.started_at = timezone.now()
                    
                # Set completed_at if transitioning to COMPLETED
                if consultation.status == 'COMPLETED' and not consultation.completed_at:
                    consultation.completed_at = timezone.now()
                    
                consultation.save()
                
                # Create notification for technician
                if consultation.requested_by:
                    Notification.objects.create(
                        user=consultation.requested_by,
                        notification_type='CONSULTATION',
                        title='Consultation Update',
                        message=f'Consultation for {consultation.patient.first_name} {consultation.patient.last_name} status updated to {consultation.get_status_display()}.',
                        related_consultation=consultation
                    )
                
                messages.success(request, "Consultation updated successfully.")
                return redirect('consultations:detail', consultation_id=consultation_id)
    else:
        # Show the appropriate form based on consultation status
        if consultation.status == 'REQUESTED' or consultation.status == 'IN_PROGRESS':
            form = ConsultationUpdateForm(instance=consultation)
            complete_form = ConsultationCompleteForm(instance=consultation)
            return render(request, 'consultations/update_consultation.html', {
                'form': form,
                'complete_form': complete_form,
                'consultation': consultation,
                'patient': consultation.patient
            })
        else:
            messages.info(request, "This consultation is already completed or cancelled.")
            return redirect('consultations:detail', consultation_id=consultation_id)
        

@login_required
def mark_notification_read(request, notification_id):
    """Mark a specific notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    
    # Redirect to related content if available
    if notification.related_consultation:
        return redirect('consultations:detail', consultation_id=notification.related_consultation.id)
    elif notification.related_tpa_request:
        return redirect('consultations:detail', consultation_id=notification.related_tpa_request.consultation.id)
    else:
        return redirect('consultations:notifications')
    

@login_required
def notifications(request):
    """View and manage user notifications"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Mark all as read if requested
    if request.method == 'POST' and 'mark_all_read' in request.POST:
        notifications.update(is_read=True)
        messages.success(request, "All notifications marked as read.")
        return redirect('consultations:notifications')
    
    return render(request, 'consultations/notifications.html', {
        'notifications': notifications,
        'unread_count': notifications.filter(is_read=False).count()
    })


@login_required
def consultation_list(request):
    """View list of consultations with filtering options"""
    # Get filter parameters
    status_filter = request.GET.get('status', None)
    
    # Base queryset
    consultations = Consultation.objects.all()
    
    # Apply filters
    if status_filter:
        consultations = consultations.filter(status=status_filter)
    
    # Filter by user role
    if hasattr(request.user, 'role'):
        if request.user.role == 'TECHNICIAN':
            # Technicians see consultations they requested
            consultations = consultations.filter(requested_by=request.user)
        elif request.user.role == 'NEUROLOGIST':
            # Neurologists see consultations assigned to them or unassigned
            consultations = consultations.filter(
                Q(neurologist=request.user) | Q(neurologist=None)
            )
    
    # Order by most recent first
    consultations = consultations.order_by('-requested_at')
    
    return render(request, 'consultations/consultation_list.html', {
        'consultations': consultations,
        'status_filter': status_filter,
    })