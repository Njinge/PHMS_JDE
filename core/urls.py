from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('patient/profile/', views.patient_profile, name='patient_profile'),
    path('patient/profile/<int:patient_id>/', views.patient_profile_view, name='patient_profile_view'),
    path('patient/lab-results/', views.patient_lab_results, name='patient_lab_results'),
    path('patient/prescriptions/', views.patient_prescriptions, name='patient_prescriptions'),
    path('patient/medical-history/', views.patient_medical_history, name='patient_medical_history'),
    path('patient/book-appointment/', views.book_appointment, name='book_appointment'),
    path('patient/appointments/', views.patient_appointments, name='patient_appointments'),
    path('doctor/appointments/', views.doctor_appointments, name='doctor_appointments'),
    path('doctor/patients/', views.doctor_patients, name='doctor_patients'),
    path('doctor/patient/<int:patient_id>/add-medical-record/', views.add_medical_record, name='add_medical_record'),
    path('doctor/patient/<int:patient_id>/add-lab-result/', views.add_lab_result, name='add_lab_result'),
    path('doctor/patient/<int:patient_id>/add-prescription/', views.add_prescription, name='add_prescription'),
    path('doctor/patient/<int:patient_id>/medical-history/', views.doctor_patient_medical_history, name='doctor_patient_medical_history'),
    path('doctor/patient/<int:patient_id>/lab-results/', views.doctor_patient_lab_results, name='doctor_patient_lab_results'),
    path('doctor/patient/<int:patient_id>/prescriptions/', views.doctor_patient_prescriptions, name='doctor_patient_prescriptions'),
    path('doctor/medical-record/<int:record_id>/edit/', views.edit_medical_record, name='edit_medical_record'),
    path('change-password/', views.change_password, name='change_password'),
] 