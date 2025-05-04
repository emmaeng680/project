from django.urls import path
from . import views

app_name = 'assessments'

urlpatterns = [
    path('nihss/perform/<int:patient_id>/', views.perform_nihss, name='perform_nihss'),
    path('nihss/details/<int:assessment_id>/', views.view_nihss_details, name='nihss_details'),
    path('nihss/perform/<int:patient_id>/', views.perform_nihss, name='perform_nihss'),
    path('nihss/detail/<int:assessment_id>/', views.view_nihss_details, name='nihss_detail'),
    path('nihss/list/', views.nihss_list, name='nihss_list'),
    path('doctor/dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    
]



