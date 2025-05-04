# from django.urls import path
# from . import views

# app_name = 'patients'

# urlpatterns = [
#     path('dashboard/', views.patient_dashboard, name='dashboard'),
#     path('list/', views.patient_list, name='list'),
#     path('register/', views.register_patient, name='register_patient'),
#     path('<int:pk>/', views.patient_detail, name='detail'),
# ]


from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    path('', views.patient_list, name='list'),
    # path('dashboard/', views.dashboard, name='dashboard'),
    path('list/', views.patient_list, name='list'),
    path('register/', views.register_patient, name='register_patient'),
    path('detail/<int:patient_id>/', views.patient_detail, name='detail'),
    # Keep additional URL patterns intact

    # New patient access URLs
    path('access/', views.patient_access, name='patient_access'),
    path('patient_dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.patient_logout, name='patient_logout'),
    path('<int:patient_id>/reset-access/', views.reset_patient_access, name='reset_access'),
]