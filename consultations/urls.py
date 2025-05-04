from django.urls import path
from . import views

app_name = 'consultations'

urlpatterns = [
    # The list view
    path('', views.consultation_list, name='list'),
    
    # Detail view
    path('<int:consultation_id>/', views.consultation_detail, name='detail'),
    
    # Update and accept views
    path('<int:consultation_id>/update/', views.update_consultation, name='update'),
    path('<int:consultation_id>/accept/', views.accept_consultation, name='accept_consultation'),
    
    # Consultation request
    path('request/<int:patient_id>/', views.request_consultation, name='request_consultation'),
    
    # TPA related
    path('tpa/request/<int:consultation_id>/', views.request_tpa, name='request_tpa'),
    path('tpa/review/<int:tpa_request_id>/', views.review_tpa, name='review_tpa'),
    path('tpa/administer/<int:tpa_request_id>/', views.administer_tpa, name='administer_tpa'),
    
    # Notifications
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    
    # Dashboards
    path('technician-dashboard/', views.technician_dashboard, name='technician_dashboard'),
    path('neurologist-dashboard/', views.neurologist_dashboard, name='neurologist_dashboard'),
]