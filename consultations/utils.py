def check_vital_signs_thresholds(vital_signs, patient):
    """
    Check vital signs against clinical thresholds and create notifications if needed
    
    Parameters:
    vital_signs: The vital signs record to check
    patient: The patient these vital signs belong to
    """
    # Import here to avoid circular imports
    from django.contrib.auth import get_user_model
    from consultations.models import Notification
    
    User = get_user_model()
    
    # Define thresholds
    systolic_min, systolic_max = 90, 185
    diastolic_min, diastolic_max = 60, 110
    heart_rate_min, heart_rate_max = 50, 120
    resp_rate_min, resp_rate_max = 10, 30
    temp_min, temp_max = 35.0, 38.5
    o2_min, o2_max = 92, 100
    glucose_min, glucose_max = 50, 400
    
    # Find users to notify
    technicians = User.objects.filter(is_technician=True)
    neurologists = User.objects.filter(is_neurologist=True)
    
    notifications = []
    
    # Systolic BP
    if vital_signs.blood_pressure_systolic < systolic_min:
        message = f"Systolic BP is critically low at {vital_signs.blood_pressure_systolic} mmHg"
        _create_notifications(technicians, neurologists, patient, message, True, notifications)
    elif vital_signs.blood_pressure_systolic > systolic_max:
        message = f"Systolic BP exceeds tPA threshold at {vital_signs.blood_pressure_systolic} mmHg"
        _create_notifications(technicians, neurologists, patient, message, True, notifications)
    
    # Diastolic BP
    if vital_signs.blood_pressure_diastolic < diastolic_min:
        message = f"Diastolic BP is critically low at {vital_signs.blood_pressure_diastolic} mmHg"
        _create_notifications(technicians, neurologists, patient, message, True, notifications)
    elif vital_signs.blood_pressure_diastolic > diastolic_max:
        message = f"Diastolic BP exceeds tPA threshold at {vital_signs.blood_pressure_diastolic} mmHg"
        _create_notifications(technicians, neurologists, patient, message, True, notifications)
    
    # Heart rate
    if vital_signs.heart_rate < heart_rate_min:
        message = f"Heart rate is critically low at {vital_signs.heart_rate} bpm"
        _create_notifications(technicians, neurologists, patient, message, False, notifications)
    elif vital_signs.heart_rate > heart_rate_max:
        message = f"Heart rate is critically elevated at {vital_signs.heart_rate} bpm"
        _create_notifications(technicians, neurologists, patient, message, False, notifications)
    
    # Respiratory rate
    if vital_signs.respiratory_rate < resp_rate_min:
        message = f"Respiratory rate is critically low at {vital_signs.respiratory_rate} br/min"
        _create_notifications(technicians, neurologists, patient, message, False, notifications)
    elif vital_signs.respiratory_rate > resp_rate_max:
        message = f"Respiratory rate is critically elevated at {vital_signs.respiratory_rate} br/min"
        _create_notifications(technicians, neurologists, patient, message, False, notifications)
    
    # Temperature
    if vital_signs.temperature < temp_min:
        message = f"Temperature is critically low at {vital_signs.temperature}°C"
        _create_notifications(technicians, neurologists, patient, message, False, notifications)
    elif vital_signs.temperature > temp_max:
        message = f"Temperature is critically elevated at {vital_signs.temperature}°C"
        _create_notifications(technicians, neurologists, patient, message, False, notifications)
    
    # Oxygen saturation
    if vital_signs.oxygen_saturation < o2_min:
        message = f"Oxygen saturation is critically low at {vital_signs.oxygen_saturation}%"
        _create_notifications(technicians, neurologists, patient, message, True, notifications)
    
    # Blood glucose (if provided)
    if vital_signs.blood_glucose is not None:
        if vital_signs.blood_glucose < glucose_min:
            message = f"Blood glucose is critically low at {vital_signs.blood_glucose} mg/dL"
            _create_notifications(technicians, neurologists, patient, message, True, notifications)
        elif vital_signs.blood_glucose > glucose_max:
            message = f"Blood glucose exceeds tPA threshold at {vital_signs.blood_glucose} mg/dL"
            _create_notifications(technicians, neurologists, patient, message, True, notifications)
    
    return notifications

def _create_notifications(technicians, neurologists, patient, message, is_critical, notifications_list):
    """Helper function to create notifications for users"""
    from consultations.models import Notification
    from django.urls import reverse
    
    # Create patient URL for linking in notifications
    patient_url = reverse('patients:detail', kwargs={'patient_id': patient.id})
    
    # Always notify technicians
    for tech in technicians:
        notification = Notification(
            user=tech,
            notification_type='SYSTEM',
            title=f"Abnormal Vital Sign - {patient.first_name} {patient.last_name}",
            message=f"{message} for patient {patient.first_name} {patient.last_name}. Immediate attention may be required.",
            related_url=patient_url
        )
        notification.save()
        notifications_list.append(notification)
    
    # Notify neurologists for critical values
    if is_critical:
        for neuro in neurologists:
            notification = Notification(
                user=neuro,
                notification_type='SYSTEM',
                title=f"CRITICAL Vital Sign - {patient.first_name} {patient.last_name}",
                message=f"CRITICAL: {message} for patient {patient.first_name} {patient.last_name}. Immediate assessment required.",
                related_url=patient_url
            )
            notification.save()
            notifications_list.append(notification)